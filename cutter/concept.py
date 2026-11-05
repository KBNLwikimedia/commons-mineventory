"""The Commons concept of a cut-out (functional design, chapter 9): file name,
description, caption, date, maker, source, licence, categories, depicts,
rights label and the choice PNG or JPG; and from that the wikitext and the
structured data (SDC) for the new file page.

Free and local: composing a concept calls nothing. The check before upload
(9.1, step 3) only reads from Commons. Uploading itself is phase 2.
"""

import re

from . import rechten, wikitekst

MAX_NAME_BYTES = 240  # 9.2; Commons allows 255 bytes, the margin is for "(2)" and the like
MAX_CAPTION = 250  # characters per caption (9.4)
# A category name may not hold the characters Commons forbids in titles, nor line breaks.
CATEGORY_FORBIDDEN = re.compile(r"[#<>\[\]{}|\n\r\x00-\x1f\x7f]")
FORBIDDEN = re.compile(r"[#<>\[\]{}|/\\:\x00-\x1f\x7f]")
TRACKING_CATEGORY = "Uploaded with Commons Mineventory"
UPLOAD_SUMMARY = (
    "Uitsnede uit [[{original}]] met de [[Commons:Commons Mineventory|Commons Mineventory]]; beschrijving deels "
    "opgesteld met een taalmodel en gecontroleerd door de uploader."
)
# Fields of {{Artwork}}, {{Photograph}}, {{Book}} and {{Map}} in the concept of a
# cut-out (9.3; decided with Olaf 4-11-2026, docs/artwork-velden.md). A cut-out is
# a detail of the same physical object: what is said about the object as a whole
# is kept; what is said about what is visible, or its size, is filled in anew or left out.
KEPT_FIELDS = (
    "artist", "author", "photographer", "illustrator", "medium", "institution", "department",
    "accession number", "credit line", "object history", "references", "object type",
    "place of creation", "place of discovery", "notes",
    # Not in the documentation of {{Artwork}}, but used by the KB for prints.
    "publisher", "place of publication", "printer",
)
TEMPLATE_FIELDS = {
    "photograph": ("camera coord",),
    # The book stays the book: its title and data are those of the original.
    "book": (
        "translator", "editor", "title", "subtitle", "series title", "volume", "edition", "city",
        "language", "isbn", "lccn", "oclc", "wikisource",
    ),
    # {{Art Photo}}: an artwork and the photo of it; both licences and the photo's date hold for a detail.
    "art photo": ("photo date", "artwork license", "photo license"),
    # A detail of a map has the same map date, sheet and scale; not its centre (latitude/longitude).
    "map": ("map date", "print date", "location", "wikidata location", "set", "sheet", "scale", "projection", "heading", "language"),
}
# Aliases from the template documentation (after "_" → " "), per template.
ALIASES = {
    "year": "date", "publication date": "date", "technique": "medium", "material": "medium",
    "size": "dimensions", "gallery": "institution", "museum": "institution", "id": "accession number",
    "other fields": "other_fields", "other versions": "other_versions",
}
ARTWORK_ALIASES = {"location": "department"}  # in {{Map}}, location is the depicted place
# The order of the fields in the new template, as in the templates' documentation.
FIELD_ORDER = (
    "artist", "author", "photographer", "illustrator", "translator", "editor", "title", "subtitle",
    "series title", "volume", "edition", "object type", "description", "depicted part", "date", "map date",
    "print date", "medium", "institution", "department", "accession number", "place of creation",
    "place of discovery", "publisher", "place of publication", "printer", "city", "language", "location",
    "wikidata location", "set", "sheet", "scale", "projection", "heading", "camera coord", "object history",
    "credit line", "inscriptions", "notes", "references", "isbn", "lccn", "oclc", "wikisource", "source",
    "permission", "other_versions", "wikidata", "other_fields",
    "photo date", "artwork license", "photo license",
)
# {{Information field}} rows in other_fields that are about the whole picture, not the object.
PICTURE_FIELD_NAMES = ("depicted", "persons related")
# A cut-out of a file in one of these categories goes into its own category (Olaf, 4-11-2026);
# the original's category itself is not taken over. The partner's source template comes
# along in |source=, with category= pointing to the cut-out category: the credit stays,
# the template itself is not changed.
PARTNERS = {
    "Media contributed by Koninklijke Bibliotheek": ("Koninklijke Bibliotheek", "Cut-outs from media contributed by Koninklijke Bibliotheek"),
    "Media from Delpher": ("Delpher", "Cut-outs from media from Delpher"),
}
CUTOUT_CATEGORIES = {partner: category for partner, (_template, category) in PARTNERS.items()}
PARTNER_TEMPLATES = {category: template for _partner, (template, category) in PARTNERS.items()}
# Statements copied from the original (9.4).
COPIED_PROPERTIES = ("P6216", "P275", "P170", "P571", "P195")
FORMATS = ("jpg", "png")
EDITABLE = {
    "bestandsnaam", "formaat", "beschrijving", "caption", "datum", "maker", "categorieen",
    "beeldt_af", "image_extracted", "merk_bevestigd", "gekozen", "sdc_waarden",
}
# Statements from the original whose values can be changed in the app (not their
# qualifiers or references; fine-tuning is for Commons itself, after the upload).
# The facts of the file (P31, P1163, P4092, P3575, P2048, P2049) are not edited.
EDITABLE_PROPERTIES = COPIED_PROPERTIES
GREGORIAN = "http://www.wikidata.org/entity/Q1985727"


def clean_name(text):
    """A file-name part without the characters Commons forbids, single-spaced,
    starting with a capital."""
    text = " ".join(FORBIDDEN.sub("-", text or "").split()).strip(" .-")
    return text[:1].upper() + text[1:]


def _cut_to_bytes(text, limit):
    encoded = text.encode("utf-8")
    if len(encoded) <= limit:
        return text
    ellipsis = "…"
    room = limit - len(ellipsis.encode("utf-8"))
    return encoded[:room].decode("utf-8", errors="ignore").rstrip(" .-(") + ellipsis


def filename(subject, original_title, extension, number=None):
    """'<Subject> – extracted from <original without extension>.<ext>' (9.2),
    at most MAX_NAME_BYTES bytes: the original's title is shortened, the
    subject is not. A collision adds a number: 'Subject (2) – …'."""
    subject = clean_name(subject) or "Detail"
    if number and number > 1:
        subject = f"{subject} ({number})"
    original = original_title.split(":", 1)[-1]
    stem = original.rsplit(".", 1)[0] if "." in original else original
    head = f"{subject} – extracted from "
    tail = f".{extension}"
    room = MAX_NAME_BYTES - len(head.encode()) - len(tail.encode())
    if room < 10:  # a very long subject: then the subject is cut after all
        return _cut_to_bytes(subject, MAX_NAME_BYTES - len(tail.encode())) + tail
    return head + _cut_to_bytes(clean_name(stem), room) + tail


def subject_of(obj):
    """The English subject (9.2): the Wikidata label of a region, else the
    English subject from "Wat staat hierop?", else the English SAM label."""
    if obj.get("bron") == "commons" and obj.get("label_en"):
        return obj["label_en"]
    description = obj.get("beschrijving") or {}
    if description.get("onderwerp_en"):
        return description["onderwerp_en"]
    label = obj.get("label") or "detail"
    return "Detail" if label in ("klik", "rechthoek", "regio") else label


MAKER_FIELDS = ("author", "artist", "photographer", "illustrator")


def date_and_maker(file, params):
    """Date and maker of the original, with where they come from (for the UI):
    the information template first (verbatim), then the file's own SDC (P571
    date, P170 maker), then the Wikidata item of the work (|wikidata= in the
    template: P577/P571, P170/P50/P110). An unknown maker becomes {{Unknown|author}}."""
    from . import sdc

    work = file.get("werk") or {}
    sources = {}
    date = params.get("date", "")
    if date:
        sources["datum"] = {"bron": "wikitekst"}
    else:
        date = sdc.first_date((file.get("_sdc") or {}).get("datum")) or ""
        if date:
            sources["datum"] = {"bron": "sdc", "eigenschap": "P571"}
        elif work.get("datum"):
            date = work["datum"]
            sources["datum"] = {"bron": "wikidata", "item": work["wikidata"], "eigenschap": work["datum_eigenschap"]}
    maker = next((params[k] for k in MAKER_FIELDS if params.get(k)), "")
    if maker:
        sources["maker"] = {"bron": "wikitekst"}
    else:
        sdc_makers = [m["label"] for m in (file.get("sdc") or {}).get("maker", []) if m.get("soort") == "item" and m.get("label")]
        if sdc_makers:
            maker = ", ".join(sdc_makers)
            sources["maker"] = {"bron": "sdc", "eigenschap": "P170"}
        elif work.get("makers"):
            maker = ", ".join(work["makers"])
            sources["maker"] = {"bron": "wikidata", "item": work["wikidata"], "eigenschap": work["maker_eigenschap"]}
        elif work.get("maker_onbekend"):
            maker = "{{Unknown|author}}"
            sources["maker"] = {"bron": "wikidata", "item": work["wikidata"], "eigenschap": "onbekend"}
    return date, maker, sources


def categories_of(file):
    """The original's categories, chosen; a partner category such as *Media
    contributed by Koninklijke Bibliotheek* (often hidden) becomes the category
    for cut-outs of that partner instead. Other categories: the user adds them."""
    shown = file.get("categorieen", [])
    hidden = file.get("verborgen_categorieen", [])
    names = [c for c in shown if c not in CUTOUT_CATEGORIES]
    names += [CUTOUT_CATEGORIES[c] for c in (*shown, *hidden) if c in CUTOUT_CATEGORIES]
    return [{"naam": c, "gekozen": True} for c in dict.fromkeys(names)]


def default_concept(file, obj):
    """The proposal for an object, from the original and the object (free)."""
    text = file.get("_wikitekst") or ""
    info = wikitekst.info_template(text)
    params = canonical_fields(info)[0] if info else {}  # |year=, |Publication date= … count as the date
    description = obj.get("beschrijving") or {}
    label_nl = obj.get("label_nl") or obj.get("label")
    caption = obj.get("bijschrift") or {}
    date, maker, sources = date_and_maker(file, params)
    depicts = []
    if obj.get("wikidata"):
        depicts.append({"q": obj["wikidata"], "label": obj.get("label")})
    return {
        "bestandsnaam": filename(subject_of(obj), file["titel"], "jpg"),
        "formaat": "jpg",
        "beschrijving": {
            "nl": description.get("beschrijving") or caption.get("tekst") or (label_nl or "").capitalize(),
            "en": description.get("beschrijving_en") or "",
        },
        "caption": {
            "nl": (description.get("onderwerp") or label_nl or "")[:MAX_CAPTION],
            "en": (description.get("onderwerp_en") or obj.get("label_en") or "")[:MAX_CAPTION],
        },
        "datum": date,
        "maker": maker,
        "herkomst": sources,
        "permissie": params.get("permission", ""),
        "licentie": wikitekst.license_templates(text),
        "categorieen": categories_of(file),
        # The text in the cut-out itself, for |inscriptions= (AI; Olaf, 4-11-2026: always).
        "inscripties": (description.get("tekst_in_beeld") or "").strip(),
        # The text just outside the cut-out on the original (a caption, a title), for |inscriptions=.
        "tekst_rond": (description.get("tekst_rond_beeld") or "").strip(),
        "beeldt_af": depicts,
        "image_extracted": True,
        "merk_bevestigd": None,
        "gekozen": None,
    }


def concept(file, obj, facts=None, page=None):
    """The concept of an object: the proposal with the user's changes
    (`obj["commons"]`) on top, plus the derived rights label, wikitext and SDC.
    `facts` (size, checksum, dimensions of the cut-out file) complete the SDC;
    with `page` (its size) comes what the original would get as region."""
    result = default_concept(file, obj)
    stored = obj.get("commons") or {}
    for key, value in stored.items():
        if key in EDITABLE:
            result[key] = value
    # The extension follows the format; a name the user typed keeps its stem.
    stem = result["bestandsnaam"].rsplit(".", 1)[0]
    result["bestandsnaam"] = f"{stem}.{result['formaat']}"
    labels = rechten.object_labels(file.get("rechten") or {}, obj)
    if result.get("merk_bevestigd") and "merk" in labels["labels"]:
        labels["merk_bevestigd"] = result["merk_bevestigd"]
    result["rechten"] = labels
    checked = rechten.default_checked(labels["labels"]) and (file.get("rechten") or {}).get("upload_toegestaan", True)
    result["gekozen"] = checked if result.get("gekozen") is None else bool(result["gekozen"])
    result["upload_toegestaan"] = (file.get("rechten") or {}).get("upload_toegestaan", True) and (
        "merk" not in labels["labels"] or bool(result.get("merk_bevestigd"))
    )
    result["wikitekst"] = wikitext(file, result)
    result["sdc"] = structured_data(file, result, facts)
    result["origineel"] = original_regions(file, page, obj, result)
    result["samenvatting"] = UPLOAD_SUMMARY.format(original=file["titel"])
    return result


def validate_patch(body):
    """The editable fields of a PATCH, checked; raises ValueError (Dutch) otherwise."""
    if not isinstance(body, dict) or not body:
        raise ValueError("Geef de velden die je wilt wijzigen.")
    unknown = set(body) - EDITABLE
    if unknown:
        raise ValueError(f"Niet te wijzigen: {', '.join(sorted(unknown))}. Wel: {', '.join(sorted(EDITABLE))}.")
    if "formaat" in body and body["formaat"] not in FORMATS:
        raise ValueError("'formaat' is 'jpg' of 'png'.")
    if "bestandsnaam" in body:
        name = body["bestandsnaam"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError("'bestandsnaam' mag niet leeg zijn.")
        if FORBIDDEN.search(name):
            raise ValueError("De bestandsnaam bevat tekens die Commons niet toestaat: # < > [ ] { } | / \\ :")
        if len(name.encode("utf-8")) > 255:
            raise ValueError("De bestandsnaam is langer dan 255 bytes.")
    for key in ("datum", "maker"):
        if key in body and not isinstance(body[key], str):
            raise ValueError(f"'{key}' is een tekst.")
    if "gekozen" in body and body["gekozen"] is not None and not isinstance(body["gekozen"], bool):
        raise ValueError("'gekozen' is true, false of null.")
    for key in ("beschrijving", "caption"):
        if key in body:
            value = body[key]
            if not isinstance(value, dict) or not set(value) <= {"nl", "en"} or not all(isinstance(v, str) for v in value.values()):
                raise ValueError(f"'{key}' is een object met teksten per taal, bijv. {{\"nl\": \"…\", \"en\": \"…\"}}.")
            if key == "caption" and any(len(v) > MAX_CAPTION for v in value.values()):
                raise ValueError(f"Een caption is hooguit {MAX_CAPTION} tekens.")
    if "categorieen" in body and not (
        isinstance(body["categorieen"], list) and all(isinstance(c, dict) and isinstance(c.get("naam"), str) for c in body["categorieen"])
    ):
        raise ValueError("'categorieen' is een lijst van {\"naam\": …, \"gekozen\": true|false}.")
    for category in body.get("categorieen") or []:
        if CATEGORY_FORBIDDEN.search(category["naam"]) or not category["naam"].strip() or len(category["naam"].encode()) > 240:
            raise ValueError(f"'{category['naam']}' is geen geldige categorienaam.")
    if "beeldt_af" in body and not (
        isinstance(body["beeldt_af"], list) and all(isinstance(d, dict) and re.fullmatch(r"Q\d+", str(d.get("q", ""))) for d in body["beeldt_af"])
    ):
        raise ValueError("'beeldt_af' is een lijst van {\"q\": \"Q…\", \"label\": …}.")
    for key in ("image_extracted",):
        if key in body and not isinstance(body[key], bool):
            raise ValueError(f"'{key}' is true of false.")
    if "sdc_waarden" in body:
        _validate_sdc_values(body["sdc_waarden"])
    if "merk_bevestigd" in body and body["merk_bevestigd"] is not None and not (
        isinstance(body["merk_bevestigd"], str) and body["merk_bevestigd"].strip()
    ):
        raise ValueError("'merk_bevestigd' is een reden (tekst), of null.")
    return body


def _validate_sdc_values(values):
    """{"P195": [{"item": "Q…"}], "P571": [{"tijd": "1708"}], "P170": [{"onbekend": true}], …};
    each value may name "bron", the index of the original statement whose qualifiers it keeps."""
    if not isinstance(values, dict):
        raise ValueError("'sdc_waarden' is een object met per eigenschap een lijst waarden.")
    for prop, items in values.items():
        if prop not in EDITABLE_PROPERTIES:
            raise ValueError(f"De waarden van {prop} zijn hier niet te wijzigen; wel van {', '.join(EDITABLE_PROPERTIES)}.")
        if not isinstance(items, list):
            raise ValueError(f"'sdc_waarden.{prop}' is een lijst.")
        for value in items:
            kinds = [k for k in ("item", "tijd", "onbekend") if k in (value if isinstance(value, dict) else {})]
            if len(kinds) != 1:
                raise ValueError("Een waarde is {\"item\": \"Q…\"}, {\"tijd\": \"1708\"} of {\"onbekend\": true}.")
            if "item" in value and not re.fullmatch(r"Q\d+", str(value["item"])):
                raise ValueError(f"'{value['item']}' is geen Wikidata-item (Q…).")
            if "tijd" in value and time_value(value["tijd"]) is None:
                raise ValueError(f"'{value['tijd']}' is geen datum; gebruik bijv. 1708, 1708-02 of 1708-02-28.")
            if "bron" in value and not (isinstance(value["bron"], int) and not isinstance(value["bron"], bool) and value["bron"] >= 0):
                raise ValueError("'bron' is het volgnummer van een statement van het origineel.")


def time_value(text):
    """A Wikibase time from "1708", "1708-02" or "1708-02-28" (year, month or day
    precision, Gregorian); None when it is not such a date."""
    match = re.fullmatch(r"\s*(-?\d{1,4})(?:-(\d{2}))?(?:-(\d{2}))?\s*", str(text or ""))
    if not match:
        return None
    year, month, day = match.group(1), match.group(2), match.group(3)
    if (month and not 1 <= int(month) <= 12) or (day and not 1 <= int(day) <= 31):
        return None
    sign = "-" if year.startswith("-") else "+"
    return {
        "time": f"{sign}{int(year.lstrip('-')):04d}-{month or '00'}-{day or '00'}T00:00:00Z",
        "timezone": 0, "before": 0, "after": 0,
        "precision": 11 if day else 10 if month else 9,
        "calendarmodel": GREGORIAN,
    }


def _value_snak(prop, value):
    if value.get("onbekend"):
        return {"snaktype": "somevalue", "property": prop}
    if "tijd" in value:
        return {"snaktype": "value", "property": prop, "datavalue": {"value": time_value(value["tijd"]), "type": "time"}}
    return _item_snak(prop, value["item"])


# -- Wikitext (9.3) ---------------------------------------------------------------------


# Characters that mean something in wikitext, as HTML entities: free text (from the AI,
# from Commons fields that are text, typed by the user) shows as written and cannot
# open or close a template, link, category, signature (~~~~), magic word (__X__),
# HTML tag or table. Commons renders the entities as the characters themselves.
WIKI_ENTITIES = {"{": "&#123;", "}": "&#125;", "[": "&#91;", "]": "&#93;", "|": "&#124;", "~": "&#126;", "<": "&lt;", ">": "&gt;", "_": "&#95;", "=": "&#61;"}


def wikisafe(text):
    """Free text for a template parameter: shown literally, never interpreted."""
    text = str(text or "").replace("&", "&amp;")
    return "".join(WIKI_ENTITIES.get(ch, ch) for ch in text)


def _languages(texts):
    return "".join(f"{{{{{lang}|1={wikisafe(text.strip())}}}}}" for lang, text in texts.items() if text and text.strip())


def canonical_fields(info):
    """The template's fields under one name per field (aliases resolved, "_" as a
    space), and per name the original's own spelling. The first one wins."""
    aliases = {**ALIASES, **(ARTWORK_ALIASES if info.name in ("artwork", "photograph", "art photo") else {})}
    params, spelling = {}, {}
    for raw, value in info.params.items():
        if raw.isdigit():
            continue
        name = " ".join(raw.replace("_", " ").split())
        name = aliases.get(name, name)
        name = {"other fields": "other_fields", "other versions": "other_versions"}.get(name, name)
        if name not in params or (value and not params[name]):
            params[name] = value
            spelling[name] = info.keys.get(raw, raw)
    return params, spelling


# The read texts as {{Inscription}} (the Commons template for text on an object): the
# text in the cut-out as type "text", the text around it on the original as "caption".
INSCRIPTION_FIELD = "{{{{Information field|name={{{{int:wm-license-artwork-inscriptions}}}}|value={value}}}}}"


def _inscription(text, kind, comment=""):
    text = wikisafe(text)
    extra = f"|comment={comment}" if comment else ""
    return f"{{{{Inscription|1={text}|type={kind}|linebreaks=1{extra}}}}}"


def inscriptions(c):
    """|inscriptions= of the cut-out: what was read in it, and what is written just
    around it on the original. Empty when nothing was read."""
    parts = []
    if c.get("inscripties"):
        parts.append(_inscription(c["inscripties"], "text"))
    if c.get("tekst_rond"):
        parts.append(_inscription(c["tekst_rond"], "caption", "outside the cut-out, on the original"))
    return "".join(parts)


def object_fields(text):
    """The {{Information field}} rows of other_fields that are about the object
    (e.g. Binder/bindery), not about the whole picture (Depicted locations)."""
    kept = []
    for call in wikitekst.templates(text or ""):
        if call.name != "information field":
            continue
        field_name = (call.params.get("name") or "").lower()
        if not any(word in field_name for word in PICTURE_FIELD_NAMES):
            kept.append(call.raw)
    return "".join(kept)


def wikitext(file, c):
    """The wikitext of the new file page. {{Extracted from}} is always there
    and cannot be removed (Olaf, 3-11-2026)."""
    original = file["titel"]
    info = wikitekst.info_template(file.get("_wikitekst") or "")
    description = _languages({"nl": c["beschrijving"].get("nl", ""), "en": c["beschrijving"].get("en", "")})
    chosen = [cat["naam"].removeprefix("Category:") for cat in c["categorieen"] if cat.get("gekozen") and cat.get("naam")]
    partner_categories = [name for name in dict.fromkeys(chosen) if name in PARTNER_TEMPLATES]
    source = f"{{{{Extracted from|{original}}}}}" + "".join(
        f" {{{{{PARTNER_TEMPLATES[name]}|category=[[Category:{name}]]}}}}" for name in partner_categories
    )
    if info and info.name in ("artwork", "photograph", "book", "map", "art photo"):
        name = {"artwork": "Artwork", "photograph": "Photograph", "book": "Book", "map": "Map", "art photo": "Art Photo"}[info.name]
        params, spelling = canonical_fields(info)
        capitals = any(k[:1].isupper() for k in info.keys.values())

        def key(field):
            """The template's own spelling ({{Book}}: |Date=, {{Artwork}}: |date=)."""
            return spelling.get(field) or (field[:1].upper() + field[1:] if capitals else field)

        caption = _languages({"nl": c["caption"].get("nl", ""), "en": c["caption"].get("en", "")})
        default_maker = {"book": "author", "photograph": "photographer"}.get(info.name, "artist")
        maker_field = next((f for f in MAKER_FIELDS if f in params), default_maker)
        kept = [k for k in (*KEPT_FIELDS, *TEMPLATE_FIELDS.get(info.name, ())) if k != maker_field]
        values = {k: params[k] for k in kept if params.get(k)}
        if info.name != "book":
            # The detail's own title; with a |wikidata= of the whole work (kept) the page
            # would otherwise show the title of the whole work (Olaf, 4-11-2026).
            values["title"] = caption
        if info.name == "artwork" and caption:
            values["depicted part"] = caption
        read = inscriptions(c)
        if info.name != "book" and read:
            # The text read in and around the cut-out (AI, editable in the magnifier).
            values["inscriptions"] = read
        other = object_fields(params.get("other_fields", ""))
        if info.name == "book" and read:
            other += INSCRIPTION_FIELD.format(value=read)  # {{Book}} has no inscriptions field
        if other:
            values["other_fields"] = other
        if params.get("wikidata"):
            values["wikidata"] = params["wikidata"]
        values.update({
            maker_field: c["maker"],
            "description": description,
            "date": c["datum"],
            "source": source,
            "permission": c.get("permissie", ""),
            "other_versions": "",
        })
        # In the order of the templates' documentation; each in the original's own spelling.
        order = {field_name: i for i, field_name in enumerate(FIELD_ORDER)}
        fields = [
            f"|{spelling.get(k) or (key('other versions') if k == 'other_versions' else key(k))}={v}"
            for k, v in sorted(values.items(), key=lambda kv: order.get(kv[0], len(order)))
        ]
        info_text = "{{" + name + "\n" + "\n".join(fields) + "\n}}"
    else:
        read = inscriptions(c)
        info_text = "\n".join(
            [
                "{{Information",
                f"|description={description}",
                f"|date={c['datum']}",
                f"|source={source}",
                f"|author={c['maker']}",
                f"|permission={c.get('permissie', '')}",
                "|other versions=",
                # {{Information}} has no inscriptions field: an extra row.
                *([f"|other fields={INSCRIPTION_FIELD.format(value=read)}"] if read else []),
                "}}",
            ]
        )
    licence = "\n".join(c["licentie"]) or "<!-- Geen licentiesjabloon gevonden op het origineel: vul dit aan. -->"
    if any(n in (file.get("_wikitekst") or "").lower() for n in ("{{flickrreview", "{{licensereview")):
        licence += f"\n<!-- De licentiecontrole van het origineel geldt ook hier; zie [[:{original}]]. -->"
    # A partner's cut-out category comes from its template in |source=, not as a separate line.
    categories = [name for name in chosen if name not in PARTNER_TEMPLATES]
    lines = [
        "=={{int:filedesc}}==",
        info_text,
        "",
        "=={{int:license-header}}==",
        licence,
        "",
    ]
    lines += [f"[[Category:{name.removeprefix('Category:')}]]" for name in dict.fromkeys(categories)]
    lines.append(f"[[Category:{TRACKING_CATEGORY}]]")
    return "\n".join(lines) + "\n"


# -- Structured data (9.4) ----------------------------------------------------------------


def _item_snak(prop, qid):
    return {
        "snaktype": "value",
        "property": prop,
        "datavalue": {"value": {"entity-type": "item", "numeric-id": int(qid[1:]), "id": qid}, "type": "wikibase-entityid"},
    }


def sdc_entity_ids(data):
    """Every property and item id in structured data (claims and qualifiers),
    to look up their labels."""
    ids = []

    def snak(s):
        ids.append(s.get("property"))
        value = (s.get("datavalue") or {}).get("value")
        if isinstance(value, dict) and value.get("id"):
            ids.append(value["id"])
        if isinstance(value, dict) and str(value.get("unit", "")).startswith("http"):
            ids.append(value["unit"].rsplit("/", 1)[-1])

    for claim in data.get("claims", []):
        snak(claim.get("mainsnak") or {})
        for prop, snaks in (claim.get("qualifiers") or {}).items():
            ids.append(prop)
            for s in snaks:
                snak(s)
    return [i for i in dict.fromkeys(ids) if i]


# Statements about the file itself, as Commons bots add them after an upload.
DIGITAL_IMAGE = "Q1250322"  # instance of (P31)
UNIT_BYTE = "http://www.wikidata.org/entity/Q8799"
UNIT_PIXEL = "http://www.wikidata.org/entity/Q355198"
SHA1 = "Q13414952"  # determination method (P459) of the checksum
MEDIA_TYPES = {"jpg": "image/jpeg", "png": "image/png"}
# Qualifiers of the original that do not hold for a cut-out: "subject has role"
# (e.g. collection highlight) is about the original object.
DROPPED_QUALIFIERS = {"P2868"}


def _string_snak(prop, value):
    return {"snaktype": "value", "property": prop, "datavalue": {"value": value, "type": "string"}}


def _quantity_snak(prop, amount, unit):
    return {"snaktype": "value", "property": prop, "datavalue": {"value": {"amount": f"+{int(amount)}", "unit": unit}, "type": "quantity"}}


def _claim(snak, qualifiers=None):
    claim = {"mainsnak": snak, "type": "statement", "rank": "normal"}
    if qualifiers:
        claim["qualifiers"] = qualifiers
    return claim


def original_regions(file, page, obj, c):
    """What the original would get for this cut-out (functional design 9.4,
    phase 2: an edit on Commons, so for now only shown): per depicts item of
    the concept a P180 statement with the cut-out as region, P2677
    "pct:x,y,w,h" relative to the whole image, like the regions Commons
    already has. Items the original already shows at (about) that place are
    marked `aanwezig`. Only for single images: on a page of a PDF or DjVu a
    region has no fixed meaning. Returns None when not applicable."""
    if file.get("paginas", 1) != 1 or not page or not obj.get("box"):
        return None
    box, width, height = obj["box"], page["breedte"], page["hoogte"]
    pct = [box["x"] / width * 100, box["y"] / height * 100, box["w"] / width * 100, box["h"] / height * 100]
    position = "pct:" + ",".join(f"{round(v, 4):g}" for v in pct)
    known = {}
    for statement in (file.get("_sdc") or {}).get("beeldt_af", []):
        if statement.get("soort") == "item":
            known.setdefault(statement["waarde"], []).extend(statement["kwalificatoren"].get("P2677") or [])
    result = []
    for depicted in c["beeldt_af"]:
        present = any(_same_region(position, other, width, height) for other in known.get(depicted["q"], []))
        result.append({"q": depicted["q"], "positie": position, "aanwezig": present})
    claims = [_claim(_item_snak("P180", r["q"]), {"P2677": [_string_snak("P2677", r["positie"])]}) for r in result if not r["aanwezig"]]
    return {"regios": result, "sdc": {"labels": {}, "claims": claims}}


def _same_region(position, other, width, height, tolerance=0.01):
    """Whether two P2677 values mark (about) the same rectangle."""
    from .regios import parse_region

    a, b = parse_region(position, width, height), parse_region(other, width, height)
    if not a or not b:
        return False
    return all(abs(a[k] - b[k]) <= tolerance * (width if k in ("x", "w") else height) for k in ("x", "y", "w", "h"))


def structured_data(file, c, facts=None):
    """What one wbeditentity on the new M-id would set (9.4): captions, depicts
    (the chosen items), the statements copied from the original, and the facts of the
    file itself (instance of, media type, checksum, size, width and height)
    when `facts` ({"sha1", "bytes", "breedte", "hoogte"}) is known. The
    relation to the original stays in the wikitext for now."""
    labels = {lang: {"language": lang, "value": text[:MAX_CAPTION]} for lang, text in c["caption"].items() if text}
    claims = []
    for depicted in c["beeldt_af"]:
        claims.append(_claim(_item_snak("P180", depicted["q"])))
    parsed = file.get("_sdc") or {}
    from .sdc import PROPERTIES

    overrides = c.get("sdc_waarden") or {}
    for prop in COPIED_PROPERTIES:
        originals = []
        for statement in parsed.get(PROPERTIES[prop], []):
            if not statement.get("_mainsnak"):
                continue
            claim = {"mainsnak": statement["_mainsnak"], "type": "statement", "rank": statement.get("rang", "normal")}
            qualifiers = {k: v for k, v in (statement.get("_qualifiers") or {}).items() if k not in DROPPED_QUALIFIERS}
            if qualifiers:
                claim["qualifiers"] = qualifiers
            originals.append(claim)
        if prop not in overrides:
            claims.extend(originals)
            continue
        # Values changed in the app: the new value, with the qualifiers of the
        # original statement it replaces (none for a value that was added).
        for value in overrides[prop]:
            source = originals[value["bron"]] if isinstance(value.get("bron"), int) and value["bron"] < len(originals) else None
            claim = {"mainsnak": _value_snak(prop, value), "type": "statement", "rank": (source or {}).get("rank", "normal")}
            if source and source.get("qualifiers"):
                claim["qualifiers"] = source["qualifiers"]
            claims.append(claim)
    claims.append(_claim(_item_snak("P31", DIGITAL_IMAGE)))
    claims.append(_claim(_string_snak("P1163", MEDIA_TYPES[c["formaat"]])))
    if facts:
        claims.append(_claim(_string_snak("P4092", facts["sha1"]), {"P459": [_item_snak("P459", SHA1)]}))
        claims.append(_claim(_quantity_snak("P3575", facts["bytes"], UNIT_BYTE)))
        claims.append(_claim(_quantity_snak("P2048", facts["hoogte"], UNIT_PIXEL)))
        claims.append(_claim(_quantity_snak("P2049", facts["breedte"], UNIT_PIXEL)))
    return {"labels": labels, "claims": claims}


# -- Check before upload (9.1 step 3): read-only on Commons --------------------------------


def check(client, concepts, sha1s):
    """For each concept {oid: concept}: does the name exist, does the same
    image exist (SHA-1 of the cut-out), do the chosen categories exist.
    Only reads from Commons."""
    names = {oid: "File:" + c["bestandsnaam"] for oid, c in concepts.items()}
    categories = sorted(
        {f"Category:{cat['naam'].removeprefix('Category:')}" for c in concepts.values() for cat in c["categorieen"] if cat.get("gekozen")}
    )
    existing_names = client.titles_exist(list(names.values())) if names else {}
    existing_categories = client.titles_exist(categories) if categories else {}
    result = {}
    taken = {}
    for oid, c in concepts.items():
        name = names[oid]
        taken[name] = taken.get(name, 0) + 1
        duplicates = client.files_with_sha1(sha1s[oid]) if sha1s.get(oid) else []
        missing = [cat["naam"] for cat in c["categorieen"] if cat.get("gekozen") and not existing_categories.get(f"Category:{cat['naam'].removeprefix('Category:')}", False)]
        warnings = []
        if existing_names.get(name):
            warnings.append({"code": "exists", "detail": name, "tekst": f"Er bestaat al een bestand met de naam '{name}'."})
        if taken[name] > 1:
            warnings.append({"code": "duplicate_name", "detail": "", "tekst": "Twee uitsneden hebben dezelfde naam; geef er een een volgnummer."})
        if duplicates:
            warnings.append({"code": "duplicate", "detail": ", ".join(duplicates), "tekst": "Dezelfde afbeelding staat al op Commons: " + ", ".join(duplicates) + "."})
        if missing:
            warnings.append({"code": "missing_category", "detail": ", ".join(missing), "tekst": "Deze categorieën bestaan niet: " + ", ".join(missing) + "."})
        if not c["upload_toegestaan"]:
            warnings.append({"code": "not_allowed", "detail": "", "tekst": "Uploaden is voor deze uitsnede uitgeschakeld (rechtenlabel)."})
        result[oid] = {
            "bestandsnaam": c["bestandsnaam"],
            "naam_bestaat": bool(existing_names.get(name)),
            "dubbel_op_commons": duplicates,
            "ontbrekende_categorieen": missing,
            "waarschuwingen": warnings,
            "in_orde": not warnings,
        }
    return result
