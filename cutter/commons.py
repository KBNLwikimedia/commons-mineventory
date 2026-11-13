"""Commons adapter: find a file, read its metadata, wikitext and structured
data, and fetch page images (functional design, chapter 5).

Read-only. Every request goes through the CachedFetcher (own User-Agent, about
one request per second, cached) and carries maxlag=5. Uploading is phase 2.
"""

import io
import json
import re
import threading
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlencode, urlsplit

from PIL import Image

from . import rechten, sdc, tegels, wikitekst
from .cache import FetchError
from .opruimen import sharded
from .sdc import QID

COMMONS_HOSTS = {"commons.wikimedia.org", "commons.m.wikimedia.org"}
FILE_PAGE = "https://commons.wikimedia.org/wiki/"

# File namespace in common languages; Commons itself only knows File: and Image:.
FILE_PREFIXES = (
    "file", "image", "bestand", "afbeelding", "datei", "bild", "fichier", "archivo", "imagen",
    "plik", "файл", "immagine", "ficheiro", "arquivo", "fil", "tiedosto", "soubor",
)

# Thumbnail widths Commons serves as standard steps (functional design 5.2).
# Checked on 3-11-2026: a request for another width comes back as the next
# step up (see tests/fixtures/commons). Up to the original width.
THUMB_STEPS = (20, 40, 60, 120, 250, 330, 500, 960, 1280, 1920, 3840)

SUPPORTED = {"image/jpeg", "image/png", "image/webp", "image/tiff", "application/pdf", "image/vnd.djvu"}
PAGED = {"application/pdf", "image/vnd.djvu", "image/tiff"}
RENDERED = {"application/pdf", "image/vnd.djvu"}  # pages come from Commons' renderer (5.4)

EXTMETADATA = (
    "LicenseShortName|License|LicenseUrl|UsageTerms|Artist|Credit|ImageDescription|DateTimeOriginal|"
    "Attribution|AttributionRequired|Restrictions|Copyrighted|ObjectName"
)


class CommonsError(Exception):
    """A user-facing error about the Commons input or file (message in Dutch)."""

    def __init__(self, message, status=400, code=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code or {400: "bad_input", 404: "not_found", 415: "unsupported", 422: "not_commons"}.get(status, "error")


# -- Input ------------------------------------------------------------------------------


def _file_title(name):
    """'File:Name.jpg' from a name with or without a (localised) prefix."""
    name = " ".join(unquote(name).replace("_", " ").split()).strip()
    prefix, sep, rest = name.partition(":")
    if sep and prefix.strip().lower() in FILE_PREFIXES:
        name = rest.strip()
    if not name:
        return None
    return "File:" + name[0].upper() + name[1:]


def parse_input(text):
    """What the user pasted (5.1), as {"titel": "File:…"} or {"pageid": n}.

    Accepts a file page URL (also /w/index.php?title=…, ?curid=…, other
    languages and #fragments), a direct or thumbnail link on
    upload.wikimedia.org, a title with or without File:, and an M-id or curid.
    """
    text = (text or "").strip()
    if not text:
        raise CommonsError("Geef een Commons-URL, een bestandsnaam of een M-id.", code="empty_input")
    match = re.fullmatch(r"[Mm](\d+)", text)
    if match:
        return {"pageid": int(match.group(1))}
    match = re.fullmatch(r"(?:curid=)?(\d+)", text)
    if match:
        return {"pageid": int(match.group(1))}
    if re.match(r"^(https?:)?//", text) or re.match(r"^[\w.-]+\.(org|net)/", text):
        return _parse_url(text if "//" in text else "https://" + text)
    title = _file_title(text.split("#")[0])
    if not title:
        raise CommonsError("Geef een Commons-URL, een bestandsnaam of een M-id.", code="empty_input")
    return {"titel": title}


def _parse_url(url):
    parts = urlsplit(url if not url.startswith("//") else "https:" + url)
    host = (parts.hostname or "").lower()
    query = parse_qs(parts.query)
    if host == "upload.wikimedia.org":
        segments = [unquote(s) for s in parts.path.split("/") if s]
        if len(segments) < 2 or segments[0] != "wikipedia" or segments[1] != "commons":
            raise CommonsError(
                "Dit bestand staat niet op Commons maar op een andere wiki. "
                "Gebruik een bestand op Commons, bijvoorbeeld https://commons.wikimedia.org/wiki/File:Example.jpg.",
                status=422,
            )
        rest = segments[2:]
        if rest and rest[0] in ("thumb", "archive", "temp"):
            rest = rest[1:]
        # Hash directories (a/ab), then the file name; a thumbnail adds "<n>px-name".
        name = next((s for s in rest if not re.fullmatch(r"[0-9a-f]{1,2}", s)), None)
        if name and re.fullmatch(r"\d{14}!.+", name):  # archived version: timestamp!name
            name = name.split("!", 1)[1]
        if not name:
            raise CommonsError("Uit deze link kan ik geen bestandsnaam halen.")
        return {"titel": _file_title(name)}
    if "curid" in query and query["curid"][0].isdigit():
        return {"pageid": int(query["curid"][0])}
    if "title" in query:
        title = _file_title(query["title"][0])
    elif parts.path.startswith("/wiki/"):
        title = _file_title(parts.path[len("/wiki/") :])
    else:
        title = None
    if not title:
        raise CommonsError("Uit deze link kan ik geen bestandsnaam halen.")
    if host not in COMMONS_HOSTS and not host.endswith((".wikipedia.org", ".wikimedia.org", ".wikisource.org", ".wikidata.org")):
        raise CommonsError(
            "Dit is geen link naar Wikimedia Commons. Gebruik bijvoorbeeld "
            "https://commons.wikimedia.org/wiki/File:Example.jpg.",
            status=422,
        )
    # A File: page on another wiki usually shows a Commons file; it is looked
    # up on Commons, and reported when it is not there.
    return {"titel": title, "andere_wiki": host if host not in COMMONS_HOSTS else None}


def snap_width(width, maximum=None):
    """The smallest standard thumbnail step of at least `width`, never wider than `maximum`."""
    step = next((s for s in THUMB_STEPS if s >= width), THUMB_STEPS[-1])
    return min(step, maximum) if maximum else step


def _plain(value, limit=None):
    if isinstance(value, dict):
        value = value.get("value")
    return wikitekst.plain_text(str(value or ""), limit) or None


# -- Client -----------------------------------------------------------------------------


class CommonsClient:
    def __init__(self, fetcher, api="https://commons.wikimedia.org/w/api.php",
                 wikidata_api="https://www.wikidata.org/w/api.php", cache_dir=None,
                 max_age=86400, max_megapixels=100):
        self.fetcher = fetcher
        self.api = api
        self.wikidata_api = wikidata_api
        self.max_age = max_age
        self.max_megapixels = max_megapixels
        self._local = threading.local()  # "read again": no cached answers in this thread
        self.originals_dir = Path(cache_dir) / "originelen" if cache_dir else None

    # -- Requests ------------------------------------------------------------------------

    def _age(self):
        """How old a cached answer may be: 0 while reading a file again (fresh())."""
        return 0 if getattr(self._local, "fresh", False) else self.max_age

    @contextmanager
    def fresh(self):
        """Read from Commons again, not from the cache (button "Read again from Commons"):
        for a caption or depicts someone just added. The answers replace the cached ones."""
        self._local.fresh = True
        try:
            yield
        finally:
            self._local.fresh = False

    def api_url(self, params, api=None):
        """GET URL for the Action API, with fixed parameters first (stable cache keys)."""
        base = {"action": "query", "format": "json", "formatversion": "2", "maxlag": "5"}
        return f"{api or self.api}?" + urlencode({**base, **params}, safe="|:")

    def _json(self, params, api=None):
        url = self.api_url(params, api)
        data = json.loads(self.fetcher.get(url, max_age=self._age()))
        if "error" in data:
            raise CommonsError(f"Commons gaf een fout: {data['error'].get('info', data['error'].get('code'))}", status=502, code="commons_error")
        return data

    # -- File --------------------------------------------------------------------------

    def file_query(self, ref):
        params = {
            "prop": "info|imageinfo|revisions|categories",
            "redirects": "1",
            "iiprop": "url|size|mime|sha1|extmetadata|bitdepth",
            "iiextmetadatafilter": EXTMETADATA,
            "iiextmetadatalanguage": "en",
            "rvprop": "content|ids",
            "rvslots": "main",
            "clprop": "hidden",
            "cllimit": "max",
        }
        if "pageid" in ref:
            params["pageids"] = str(ref["pageid"])
        else:
            params["titles"] = ref["titel"]
        return self._json(params)

    def load_file(self, text_or_ref):
        """The file (5.2): title, M-id, size, MIME, SHA-1, licence, maker,
        categories, SDC and rights labels. Raises CommonsError (404) when it
        does not exist on Commons."""
        ref = parse_input(text_or_ref) if isinstance(text_or_ref, str) else text_or_ref
        data = self.file_query(ref)
        query = data.get("query") or {}
        pages = query.get("pages") or []
        page = pages[0] if pages else {}
        wanted = ref.get("titel") or f"M{ref.get('pageid')}"
        if not page or page.get("missing") or page.get("invalid") or "imageinfo" not in page:
            where = f" (gevonden op {ref['andere_wiki']}, maar niet op Commons)" if ref.get("andere_wiki") else ""
            raise CommonsError(
                f"Het bestand '{wanted}' bestaat niet op Wikimedia Commons{where}. "
                "Voorbeeld: https://commons.wikimedia.org/wiki/File:Example.jpg",
                status=404,
            )
        if page.get("ns") != 6:
            raise CommonsError(f"'{page.get('title')}' is geen bestand (File:).", status=422, code="not_a_file")
        redirected = next((r["from"] for r in query.get("redirects") or []), None)
        info = page["imageinfo"][0]
        meta = info.get("extmetadata") or {}
        revision = (page.get("revisions") or [{}])[0]
        text = ((revision.get("slots") or {}).get("main") or {}).get("content", "")
        categories = page.get("categories") or []
        mime = info.get("mime", "")
        mid = f"M{page['pageid']}"
        parsed_sdc = self.entity(mid)
        labels = self.labels(sdc.item_ids(parsed_sdc))
        work = self._work_for(text, parsed_sdc)
        width, height = info.get("width", 0), info.get("height", 0)
        pages_count = info.get("pagecount") or 1
        supported, reason = self._supported(mime, width, height)
        file = {
            "mid": mid,
            "pageid": page["pageid"],
            "titel": page["title"],
            "naam": page["title"].split(":", 1)[1],
            "url": FILE_PAGE + quote(page["title"].replace(" ", "_"), safe=":()',"),
            "origineel_url": info.get("url"),
            "breedte": width,
            "hoogte": height,
            "megapixels": round(width * height / 1e6, 1),
            "mime": mime,
            "sha1": info.get("sha1"),
            "grootte_bytes": info.get("size"),
            "bitdiepte": info.get("bitdepth"),
            "paginas": pages_count if mime in PAGED else 1,
            "ondersteund": supported,
            "niet_ondersteund": reason,
            # The same as a code (svg, gif, media, type), for the interface in any language.
            "niet_ondersteund_code": self._unsupported_code(mime),
            # Above MAX_MEGAPIXELS: cut-outs in pieces with libvips (cutter/tegels.py), when installed.
            "uitsnijden_mogelijk": supported and (mime in RENDERED or width * height <= self.max_megapixels * 1e6 or tegels.available()),
            "tegels": supported and mime not in RENDERED and width * height > self.max_megapixels * 1e6 and tegels.available(),
            "revisie": revision.get("revid"),
            "doorverwezen_van": redirected,
            "licentie": {
                "kort": _plain(meta.get("LicenseShortName")),
                "url": _plain(meta.get("LicenseUrl")),
                "voorwaarden": _plain(meta.get("UsageTerms")),
                "sjablonen": wikitekst.license_templates(text),
            },
            "maker": _plain(meta.get("Artist"), 300),
            "naamsvermelding": _plain(meta.get("Attribution"), 300) or _plain(meta.get("Credit"), 300),
            "datum": _plain(meta.get("DateTimeOriginal"), 100),
            "beschrijving": _plain(meta.get("ImageDescription"), 2000),
            "categorieen": [c["title"].split(":", 1)[1] for c in categories if not c.get("hidden")],
            "verborgen_categorieen": [c["title"].split(":", 1)[1] for c in categories if c.get("hidden")],
            "sdc": sdc.summary(parsed_sdc, labels),
            "rechten": rechten.file_labels(text, {k: _plain(v) for k, v in meta.items()}, parsed_sdc),
            "bestaande_uitsneden": wikitekst.extracted_files(text),
            "regio_aantal": sum(
                1 for s in parsed_sdc.get("beeldt_af", []) for p in s["kwalificatoren"].get("P2677") or [] if p
            ),
            "notitie_aantal": len(wikitekst.image_notes(text)),
            "werk": work,
            # Internal (not in the API): the raw material for regions and the concept.
            "_wikitekst": text,
            "_sdc": parsed_sdc,
            "_labels": labels,
        }
        return file

    def _work_for(self, text, parsed_sdc=None):
        """The Wikidata item of the work, looked up; None without one. Like
        {{Artwork}} itself: |wikidata= in the information template, else the
        file's SDC "digital representation of" (P6243)."""
        info = wikitekst.info_template(text)
        qid = (info.params.get("wikidata") or "").strip() if info else ""
        source = "wikitekst"
        if not QID.fullmatch(qid):
            qid = next((s["waarde"] for s in (parsed_sdc or {}).get("digitale_weergave_van", []) if s["soort"] == "item"), "")
            source = "sdc"
        if not QID.fullmatch(qid or ""):
            return None
        try:
            return {**self.work(qid), "via": source}
        except (FetchError, CommonsError):
            return {"wikidata": qid, "via": source, "label": None, "datum": None, "datum_eigenschap": None,
                    "makers": [], "maker_eigenschap": None, "maker_onbekend": False}

    UNSUPPORTED = {
        "svg": "SVG wordt niet ondersteund: snijd een vectorbestand liever uit in een tekenprogramma.",
        "gif": "GIF wordt niet ondersteund (vaak geanimeerd).",
        "media": "Video en audio worden niet ondersteund.",
        "type": "Bestandstype {mime} wordt niet ondersteund.",
    }

    def _unsupported_code(self, mime):
        """Why a file type is not supported, as a code for the interface (None: supported)."""
        if mime in SUPPORTED:
            return None
        if mime == "image/svg+xml":
            return "svg"
        if mime == "image/gif":
            return "gif"
        if mime.startswith(("video/", "audio/", "application/ogg")):
            return "media"
        return "type"

    def _supported(self, mime, width, height):
        code = self._unsupported_code(mime)
        if code is None:
            return True, None
        return False, self.UNSUPPORTED[code].format(mime=mime or "onbekend")

    def entity(self, mid):
        """The parsed MediaInfo entity (SDC) of a file; empty when it has none."""
        data = json.loads(self.fetcher.get(self.api_url({"action": "wbgetentities", "ids": mid}), max_age=self._age()))
        return sdc.parse_entity((data.get("entities") or {}).get(mid))

    def item_image(self, qid, prop="P18"):
        """The file name of the image (P18) or logo (P154) of a Wikidata item, or None. Cached."""
        return self.item_files([qid], prop).get(qid)

    def item_files(self, ids, prop="P18"):
        """{Q-id: file name} of a Commons-file property (P18 image, P154 logo) of Wikidata
        items; items without one are left out. Deprecated statements do not count. Cached."""
        found = {}
        for qid, entity in self._wikidata_entities(ids, "claims"):
            for claim in (entity.get("claims") or {}).get(prop) or []:
                value = ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value")
                if claim.get("rank") != "deprecated" and isinstance(value, str) and value:
                    found[qid] = value
                    break
        return found

    def item_thumbnail(self, qid, width=120, prop="P18"):
        """Bytes of a small thumbnail of an item's image (P18) or logo (P154), fetched through
        the server so the browser loads nothing from Wikimedia; None without one. Cached."""
        name = self.item_image(qid, prop)
        if not name:
            return None
        data = self._json({"prop": "imageinfo", "titles": f"File:{name}", "iiprop": "url", "iiurlwidth": str(width)})
        pages = (data.get("query") or {}).get("pages") or [{}]
        info = (pages[0].get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url")
        return self.fetcher.get(url) if url else None

    def _wikidata_entities(self, ids, props, pattern=QID, fallback=False):
        """(id, entity) from Wikidata's wbgetentities, 50 ids per request, cached.
        A batch that cannot be fetched is skipped: labels and descriptions are a
        nicety, the id itself stays readable."""
        ids = [i for i in dict.fromkeys(ids) if re.fullmatch(pattern, i or "")]
        for start in range(0, len(ids), 50):
            params = {"action": "wbgetentities", "ids": "|".join(ids[start : start + 50]), "props": props, "languages": "nl|en"}
            if fallback:
                params["languagefallback"] = "1"
            try:
                data = self._json(params, api=self.wikidata_api)
            except (FetchError, CommonsError):
                continue
            yield from (data.get("entities") or {}).items()

    @staticmethod
    def _texts(values):
        """{"nl": …, "en": …} from Wikibase labels or descriptions."""
        return {lang: ((values or {}).get(lang) or {}).get("value") for lang in ("nl", "en")}

    def labels(self, ids):
        """{Q-id: {"nl": label, "en": label}} from Wikidata."""
        return {qid: self._texts(entity.get("labels")) for qid, entity in self._wikidata_entities(ids, "labels")}

    def item_info(self, ids):
        """{Q-id: {"label": {nl, en}, "beschrijving": {nl, en}}} from Wikidata;
        items that cannot be fetched are left out."""
        return {
            qid: {"label": self._texts(entity.get("labels")), "beschrijving": self._texts(entity.get("descriptions"))}
            for qid, entity in self._wikidata_entities(ids, "labels|descriptions")
        }

    def entity_labels(self, ids):
        """{id: {"nl": label, "en": label}} for Wikidata items and properties
        (Q… and P…), with Wikidata's language fallback. Ids without a label are
        left out (the id stays readable)."""
        result = {}
        for eid, entity in self._wikidata_entities(ids, "labels", pattern=r"[QP]\d+", fallback=True):
            names = self._texts(entity.get("labels"))
            if any(names.values()):
                result[eid] = names
        return result

    def render_wikitext(self, text, title):
        """The HTML Commons makes of wikitext, as a preview of the file page
        (action=parse; only reads, changes nothing). POST because the text can
        be longer than a URL allows; cached by content."""
        data = {
            "action": "parse", "format": "json", "formatversion": "2", "maxlag": "5",
            "text": text, "title": title, "contentmodel": "wikitext", "prop": "text",
            "pst": "1", "disablelimitreport": "1", "disableeditsection": "1", "preview": "1",
        }
        body = json.loads(self.fetcher.post(self.api, data, max_age=self._age()))
        if "error" in body:
            raise CommonsError(f"Commons gaf een fout: {body['error'].get('info', body['error'].get('code'))}", status=502, code="commons_error")
        return (body.get("parse") or {}).get("text") or ""

    MAKER_PROPERTIES = ("P170", "P50", "P110")  # creator, author, illustrator
    # What {{Artwork}} shows from the item of the work, for the Metadata block:
    # key → property; each becomes a list of items {"id", "nl", "en"}.
    WORK_ITEMS = {
        "soort": "P31",  # instance of (object type)
        "onderdeel_van": "P361",  # part of
        "beeldt_af": "P180",  # depicts
        "materiaal": "P186",  # made from material (medium)
        "collectie": "P195",  # collection (with its P217 inventory number)
        "locatie": "P276",  # location
        "plaats": "P1071",  # location of creation
    }
    UNITS = {"Q174728": "cm", "Q174789": "mm", "Q11573": "m"}

    def work(self, qid):
        """The Wikidata item of the work the file shows (|wikidata= in {{Book}},
        {{Artwork}} …, or the file's P6243): its label, date (P577 publication
        date, else P571 inception) and makers (P170 creator, P50 author, P110
        illustrator), used when the file page itself leaves date or maker empty;
        and for the Metadata block what {{Artwork}} shows from it: title,
        description, object type, part of, depicts, material, dimensions,
        collection with inventory number, location, place of creation, links."""
        data = self._json({"action": "wbgetentities", "ids": qid, "props": "labels|descriptions|claims", "languages": "nl|en"}, api=self.wikidata_api)
        entity = (data.get("entities") or {}).get(qid) or {}
        claims = entity.get("claims") or {}

        def statements(prop):
            return [{"rang": c.get("rank"), "_mainsnak": c.get("mainsnak")} for c in claims.get(prop, [])]

        date, date_prop = None, None
        for prop in ("P577", "P571"):
            date = sdc.first_date(statements(prop))
            if date:
                date_prop = prop
                break
        maker_ids, maker_prop, unknown = [], None, False
        for prop in self.MAKER_PROPERTIES:
            snaks = [s["_mainsnak"] or {} for s in statements(prop)]
            ids = [((s.get("datavalue") or {}).get("value") or {}).get("id") for s in snaks if s.get("snaktype") == "value"]
            if any(ids):
                maker_ids, maker_prop = [i for i in ids if i], prop
                break
            unknown = unknown or any(s.get("snaktype") in ("somevalue", "novalue") for s in snaks)
        def values(prop):
            """The values of a property (preferred and normal rank), as plain data."""
            result = []
            for claim in claims.get(prop, []):
                snak = claim.get("mainsnak") or {}
                if claim.get("rank") == "deprecated" or snak.get("snaktype") != "value":
                    continue
                result.append(((snak.get("datavalue") or {}).get("value"), claim.get("qualifiers") or {}))
            return result

        def item_id(value):
            return value.get("id") if isinstance(value, dict) else None

        found = {key: [(item_id(v), q) for v, q in values(prop) if item_id(v)] for key, prop in self.WORK_ITEMS.items()}
        units = {}
        sizes = []
        for prop, key in (("P2048", "hoogte"), ("P2049", "breedte")):
            for value, _ in values(prop)[:1]:
                if isinstance(value, dict) and value.get("amount"):
                    unit = str(value.get("unit") or "").rsplit("/", 1)[-1]
                    units[key] = unit
                    sizes.append((key, value["amount"].lstrip("+"), unit))
        # The makers first (needed for the concept), then the rest in one more lookup.
        labels = self.labels(maker_ids) if maker_ids else {}
        other_ids = [i for pairs in found.values() for i, _ in pairs] + [u for u in units.values() if u not in self.UNITS and u != "1"]
        other_ids = [i for i in dict.fromkeys(other_ids) if i not in labels]
        if other_ids:
            labels = {**labels, **self.labels(other_ids)}

        def item(i):
            names = labels.get(i) or {}
            return {"id": i, "nl": names.get("nl"), "en": names.get("en")}

        def inventory(qualifiers):
            return [((s.get("datavalue") or {}).get("value")) for s in qualifiers.get("P217", []) if s.get("snaktype") == "value"]

        # The logo (P154) of a collection or location, e.g. the KB's, shown with its name (wish Olaf).
        institutions = [i for key in ("collectie", "locatie") for i, _ in found[key]]
        logos = self.item_files(institutions, "P154") if institutions else {}

        def with_logo(entry):
            return {**entry, "logo": bool(logos.get(entry["id"]))}

        collections = [with_logo({**item(i), "inventarisnummers": inventory(q)}) for i, q in found.pop("collectie")]
        locations = [with_logo(item(i)) for i, _ in found.pop("locatie")]
        # P217 as a statement of its own (with P195 as qualifier): add it to that collection, or on its own.
        loose = []
        for value, qualifiers in values("P217"):
            where = [item_id(((s.get("datavalue") or {}).get("value"))) for s in qualifiers.get("P195", [])]
            target = next((c for c in collections if c["id"] in where), None)
            if target is not None:
                if value not in target["inventarisnummers"]:
                    target["inventarisnummers"].append(value)
            elif isinstance(value, str):
                loose.append(value)
        titles = {}
        for value, _ in values("P1476"):
            if isinstance(value, dict) and value.get("text"):
                titles.setdefault(value.get("language") or "", value["text"])
        names = entity.get("labels") or {}
        descriptions = entity.get("descriptions") or {}
        return {
            "wikidata": qid,
            "label": (names.get("nl") or names.get("en") or {}).get("value"),
            "label_en": (names.get("en") or names.get("nl") or {}).get("value"),
            "titel": titles.get("nl") or titles.get("en") or next(iter(titles.values()), None),
            "beschrijving": {lang: (descriptions.get(lang) or {}).get("value") for lang in ("nl", "en")},
            "datum": date,
            "datum_eigenschap": date_prop,
            "makers": [(labels.get(i) or {}).get("nl") or (labels.get(i) or {}).get("en") or i for i in maker_ids],
            # The makers as items too, so Metadata can link them to Wikidata (wish Olaf).
            "maker_items": [item(i) for i in maker_ids],
            "maker_eigenschap": maker_prop,
            "maker_onbekend": not maker_ids and unknown,
            **{key: [item(i) for i, _ in pairs] for key, pairs in found.items()},
            "collectie": collections,
            "locatie": locations,
            "inventarisnummers": loose,
            "afmetingen": [
                {"maat": key, "waarde": amount, "eenheid": self.UNITS.get(unit) or ("" if unit == "1" else (labels.get(unit) or {}).get("en") or unit)}
                for key, amount, unit in sizes
            ],
            "links": [v for v, _ in values("P973") if isinstance(v, str) and v.startswith(("https://", "http://"))][:3],
        }

    def search_items(self, text, language="en", limit=7):
        """Wikidata items for a search term (free; 6.2): the user chooses the
        item for depicts, the model never makes up Q-ids."""
        text = " ".join((text or "").split())[:100]
        if not text:
            return []
        params = {
            "action": "wbsearchentities", "search": text, "language": language, "uselang": language,
            "type": "item", "limit": str(limit),
        }
        data = self._json(params, api=self.wikidata_api)
        return [
            {"q": hit["id"], "label": hit.get("label") or hit["id"], "beschrijving": hit.get("description")}
            for hit in data.get("search") or []
        ]

    def depicted_by_extracted(self, file):
        """Q-ids depicted (P180) on the existing cut-outs named in {{Image
        extracted}}, so regions already cut out can be marked (7.5)."""
        titles = file.get("bestaande_uitsneden") or []
        if not titles:
            return set()
        data = self._json({"titles": "|".join(titles[:50]), "prop": "info"})
        mids = [f"M{p['pageid']}" for p in (data.get("query") or {}).get("pages", []) if p.get("pageid")]
        found = set()
        for mid in mids[:20]:
            parsed = self.entity(mid)
            found |= {s["waarde"] for s in parsed.get("beeldt_af", []) if s["soort"] == "item"}
        return found

    # -- Existence checks (read-only, for the check before upload, 9.1) --------------------

    def titles_exist(self, titles):
        """{title: exists} for file or category titles (50 per request)."""
        result = {}
        for start in range(0, len(titles), 50):
            chunk = titles[start : start + 50]
            data = self._json({"titles": "|".join(chunk), "prop": "info"})
            query = data.get("query") or {}
            normalized = {n["from"]: n["to"] for n in query.get("normalized") or []}
            exists = {p["title"]: not p.get("missing") and not p.get("invalid") for p in query.get("pages", [])}
            for title in chunk:
                result[title] = exists.get(normalized.get(title, title), False)
        return result

    def files_with_sha1(self, sha1):
        """Titles of files on Commons with this SHA-1 (duplicates, 5.2 and 9.1)."""
        data = self._json({"list": "allimages", "aisha1": sha1, "aiprop": "url"})
        return [i["title"] for i in (data.get("query") or {}).get("allimages", [])]

    # -- Pages and images ----------------------------------------------------------------

    def page_ref(self, file, n):
        if not 1 <= n <= file["paginas"]:
            raise CommonsError(f"Pagina {n} bestaat niet; dit bestand heeft {file['paginas']} pagina('s).", status=404)
        return {"id": f"{file['sha1']}|{n}", "n": n}

    def load_page(self, file, n):
        """Page n with its size in native pixels: the file itself, or for PDF,
        DjVu and multi-page TIFF the page as Commons renders it at the file's width."""
        page = self.page_ref(file, n)
        if file["paginas"] == 1 and file["mime"] not in RENDERED:
            return {**page, "breedte": file["breedte"], "hoogte": file["hoogte"]}
        thumb = self._thumb_info(file, n, file["breedte"])
        return {**page, "breedte": thumb.get("thumbwidth") or file["breedte"], "hoogte": thumb.get("thumbheight") or file["hoogte"]}

    def _thumb_info(self, file, n, width):
        params = {"prop": "imageinfo", "pageids": str(file["pageid"]), "iiprop": "url|size", "iiurlwidth": str(width)}
        if file["paginas"] > 1 or file["mime"] in RENDERED:
            params["iiurlparam"] = f"page{n}-{width}px"
        data = self._json(params)
        pages = (data.get("query") or {}).get("pages") or [{}]
        return (pages[0].get("imageinfo") or [{}])[0]

    def page_image(self, file, n, width):
        """Bytes of a reduced page image, at the nearest standard step of at
        least `width` (never wider than the page). Cached."""
        page = self.load_page(file, n)
        step = snap_width(width, page["breedte"])
        thumb = self._thumb_info(file, n, step)
        url = thumb.get("thumburl") or thumb.get("url")
        if not url:
            raise CommonsError("Commons levert geen verkleinde afbeelding van dit bestand.", status=502, code="no_thumbnail")
        return self.fetcher.get(url)

    def original_image(self, file, n):
        """The page at full resolution as a PIL image (5.4): the original file
        (TIFF pages by index), or for PDF/DjVu the largest rendering by Commons.
        Used for every cut-out; the reduced images are only for viewer and model."""
        if not file.get("uitsnijden_mogelijk"):
            raise CommonsError(
                file.get("niet_ondersteund")
                or f"Dit bestand is groter dan {self.max_megapixels} megapixel; uitsnijden in volledige resolutie kan nog niet.",
                status=413,
                code="too_large",
            )
        if file["mime"] in RENDERED:
            page = self.load_page(file, n)
            thumb = self._thumb_info(file, n, page["breedte"])
            data = self.fetcher.get(thumb.get("thumburl") or thumb["url"])
            return Image.open(io.BytesIO(data))
        if file.get("tegels"):
            # Too large to decode as a whole: read in pieces from the file on disk.
            return tegels.TiledImage(self._original_path(file) or self._original_bytes(file), page=n - 1)
        data = self._original_bytes(file)
        Image.MAX_IMAGE_PIXELS = max(Image.MAX_IMAGE_PIXELS or 0, int(self.max_megapixels * 1e6 * 1.1))
        image = Image.open(io.BytesIO(data))
        if n > 1:
            image.seek(n - 1)
        return image

    def _original_path(self, file):
        """The original on disk (fetched once), or None without a cache folder."""
        if self.originals_dir is None:
            return None
        path = sharded(self.originals_dir, file["sha1"])
        if not path.exists():
            self._original_bytes(file)
        else:
            path.touch()  # retention counts from the last use (12.1)
        return path

    def _original_bytes(self, file):
        """The original file, fetched once from upload.wikimedia.org and kept
        under cache/originelen/<sha1> (cleaned up after BEWAAR_ORIGINELEN_DAGEN)."""
        if self.originals_dir is None:
            return self.fetcher.get(file["origineel_url"])
        path = sharded(self.originals_dir, file["sha1"])
        if path.exists():
            path.touch()  # retention counts from the last use (12.1)
            return path.read_bytes()
        data = self.fetcher.get(file["origineel_url"], store=False)  # kept here, not in the HTTP cache
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return data


def public(file):
    """The file as the API shows it: without the internal raw material."""
    return {k: v for k, v in file.items() if not k.startswith("_")}
