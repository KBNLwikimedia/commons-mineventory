"""Detection service: turns a request into detector calls and keeps one shared
object list per page (functional design, chapters 6 and 7). Taken over from
the Delpher Uitsnijder without zones, ALTO, captions from OCR and hierarchy.

- Each English term is one detector call; results are cached on disk per
  file SHA-1, page, term, model and image width, so repeating a search costs
  nothing, and a new version of the file gives a new detection (6.1).
- EN/AND combines terms; an object of a MIN/NOT term excludes a candidate when
  their boxes overlap with IoU >= MIN_IOU.
- "Alles detecteren", "Dubbelingen samenvoegen" and saving all use one rule for
  "the same picture" (same_picture, via _one_per_picture); regions from Commons
  are never merged.
- Regions from Commons (P180 with P2677, file notes) are free objects of their
  own; they are never merged, also not when they overlap (7.5).
- Paid calls are checked against the limits first and logged.
"""

import functools
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from .. import export, prompts, regios
from ..commons import public as public_file
from .basis import DetectionError
from ..opruimen import last_used, mark_used
from ..slot import store_lock
from ..verbruik import KOSTEN_PER_AFBEELDING
from .maskers import MaskCache, decode_raster

MIN_IOU = 0.5
DUPLICATE_IOU = 0.8
SOURCE_PREFERENCE = {"sam": 0, "dummy": 1, "handmatig": 2}  # on merging: SAM has a real mask
NEVER_MERGED = {"commons"}  # regions from Commons stay objects of their own (7.5)
# Page image width sent to the detector: the Commons thumbnail step closest to
# the 2000 px of the Delpher Uitsnijder (functional design 5.2 and 6.1).
IMAGE_WIDTH = 1920
STATUSES = ("kandidaat", "geselecteerd", "uitgesloten")
MODES = ("prompt", "alles", "commons")


def _write_atomic(path, text):
    """Write via a temporary file and a rename: readers see the old or the new file, never half."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
MAX_TERMS_PER_REQUEST = 20  # search terms in one request (each uncached term is one paid SAM call)
SAVED_META = ("tijdstempel", "breedte", "hoogte")  # in "opgeslagen", next to the file paths
# Fields made by the user or paid for, kept when a search returns an object again.
KEPT_ON_UPDATE = ("bijschrift", "ook", "beschrijving", "commons", "masker", "masker_herkomst", "status")


def iou(a, b):
    ix = max(0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    iy = max(0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    inter = ix * iy
    union = a["w"] * a["h"] + b["w"] * b["h"] - inter
    return inter / union if union else 0.0


def same_picture(a, b):
    """Whether two boxes show the same picture: they overlap with IoU >=
    DUPLICATE_IOU, or the smaller lies almost entirely (>= 90%) in the larger
    and they overlap at least half."""
    overlap = iou(a, b)
    if overlap >= DUPLICATE_IOU:
        return True
    ix = max(0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    iy = max(0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    smaller = min(a["w"] * a["h"], b["w"] * b["h"])
    return overlap >= 0.5 and smaller > 0 and ix * iy / smaller >= 0.9


def _mergeable(a, b):
    return a.get("bron") not in NEVER_MERGED and b.get("bron") not in NEVER_MERGED and same_picture(a["box"], b["box"])


def _fill_dutch_names(store):
    """Dutch names for labels that came from "Wat staat op deze pagina?": the
    page overview has a Dutch name per suggested term. Only in memory."""
    names = {t["en"]: t["nl"] for t in (store.get("inventaris") or {}).get("zoektermen", []) if t.get("nl")}
    if not names:
        return
    for obj in store.get("objecten", []) + store.get("prullenbak", []):
        label = (obj.get("label") or "").lower()
        if label in names and prompts.dutch(label) == label:
            obj["label_nl"] = names[label]


def _preference(obj):
    """Which of two objects showing the same picture to keep: SAM before dummy
    before a manual rectangle, then the highest score, then the smallest box."""
    box = obj["box"]
    return (SOURCE_PREFERENCE.get(obj.get("bron"), 3), -(obj.get("score") or 0), box["w"] * box["h"], obj["id"])


def _ids(obj):
    return [obj["id"]] + [e["id"] for e in obj.get("ook", [])]


def _sources(obj):
    return list(dict.fromkeys([obj.get("bron")] + [e.get("bron") for e in obj.get("ook", [])]))


def _summary(obj):
    return {k: obj.get(k) for k in ("id", "bron", "label", "zoekterm", "score", "box")}


def _contains(box, x, y):
    return box["x"] <= x <= box["x"] + box["w"] and box["y"] <= y <= box["y"] + box["h"]


def _locked(method):
    """Run a method that reads, changes and writes an object store as one step,
    so two requests at the same time cannot overwrite each other's change."""

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        with self.lock:
            return method(self, *args, **kwargs)

    return wrapper


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class DetectionService:
    def __init__(self, detector, client, cache_dir, output_dir, verbruik):
        self.detector = detector
        self.client = client
        self.cache_dir = Path(cache_dir) / "detectie"
        self.output_dir = Path(output_dir)
        self.verbruik = verbruik
        self.keep_cutout_days = 30  # BEWAAR_UITSNEDEN_DAGEN; set by create_app
        self.masks = MaskCache(Path(cache_dir) / "maskers")
        # One lock for all object stores (re-entrant: locked methods call each other),
        # shared with other workers and the cleanup task (see cutter/slot.py).
        self.lock = store_lock(self.output_dir)
        # Size and checksum of cut-out files, by what makes the file (see file_facts).
        self._facts = {}

    # -- Terms and planning ----------------------------------------------------

    @staticmethod
    def terms(prompt="", modus="prompt"):
        """{"plus": [{term, en}], "min": [...]} for a request."""
        if modus == "alles":
            return {"plus": [{"term": t, "en": t} for t in prompts.ALLES], "min": []}
        if modus == "commons":
            return {"plus": [], "min": []}
        if modus != "prompt":
            raise DetectionError(f"Onbekende modus '{modus}'; kies uit {', '.join(MODES)}.", status=400)
        parsed = prompts.parse_prompt(prompt)
        if not parsed["plus"]:
            raise DetectionError("Geef minstens één begrip om te zoeken, bijv. 'wapen' of 'portret'.", status=400, code="empty_prompt")
        return parsed

    def _cache_path(self, page_id, term):
        width = getattr(self.detector, "max_width", IMAGE_WIDTH)
        key = f"{page_id}|{self.detector.model}|{width}|{term}"
        digest = hashlib.sha1(key.encode()).hexdigest()
        return self.cache_dir / digest[:2] / f"{digest}.json"

    def plan(self, file, n, terms):
        """How many paid calls a request needs (cached terms are free)."""
        page_id = self.client.page_ref(file, n)["id"]
        all_terms = [t["en"] for t in terms["plus"] + terms["min"]]
        uncached = [t for t in dict.fromkeys(all_terms) if not self._cache_path(page_id, t).exists()]
        paid = len(uncached) if self.detector.betaald else 0
        return {"termen": len(set(all_terms)), "betaald": paid, "uit_cache": len(set(all_terms)) - len(uncached)}

    # -- Detection ---------------------------------------------------------------

    @_locked
    def detect(self, file, n, prompt="", modus="prompt", minscore=0.0, dry_run=False, user=None):
        terms = self.terms(prompt, modus)
        page = self.client.load_page(file, n)
        plan = self.plan(file, n, terms)
        result = {"modus": modus, "termen": terms, "aanroepen": plan, "detector": self.detector.model, "dry_run": dry_run}
        if dry_run:
            result["budget"] = self.verbruik.status(user)
            return result
        if len(terms["plus"]) + len(terms["min"]) > MAX_TERMS_PER_REQUEST:
            raise DetectionError(
                f"Hooguit {MAX_TERMS_PER_REQUEST} zoektermen per opdracht.", status=400, code="too_many_terms"
            )
        if plan["betaald"]:
            self.verbruik.check(plan["betaald"], user=user, cost=plan["betaald"] * KOSTEN_PER_AFBEELDING)

        excluded = []
        if modus == "commons":
            found = self._commons_objects(file, page)
        else:
            context = {"image": None}
            found = []
            for term in terms["plus"]:
                found += self._run_term(file, page, term, context, user)
            for term in terms["min"]:
                excluded += self._run_term(file, page, term, context, user)
            found = [o for o in found if o["score"] is None or o["score"] >= minscore]
            if modus == "alles":
                found = self._merge_duplicates(found)
        for obj in found:
            obj["status"] = "geselecteerd"
            if any(iou(obj["box"], other["box"]) >= MIN_IOU for other in excluded):
                obj["status"] = "uitgesloten"

        objects = self._merge_into_page(file, n, found)
        result.update(
            {
                "nieuw": [o["id"] for o in found],
                "objecten": [self.public(file, n, o) for o in objects],
                "niets_gevonden": not found,
                "budget": self.verbruik.status(user),
            }
        )
        return result

    def _run_term(self, file, page, term, context, user):
        """Objects for one English term: from the cache or from the detector."""
        path = self._cache_path(page["id"], term["en"])
        if path.exists():
            mark_used(path)
            stored = json.loads(path.read_text(encoding="utf-8"))
        else:
            if self.detector.betaald:
                self.verbruik.check(1, user=user, cost=KOSTEN_PER_AFBEELDING)
            detected = self.detector.detect(
                self._image(file, page, context), term["en"], native_size=(page["breedte"], page["hoogte"])
            )
            stored = [o.to_dict() for o in detected]
            if self.detector.betaald:
                self._register(file, page["n"], term["en"], user)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(stored, ensure_ascii=False), encoding="utf-8")
        return [self._stamp(page, term, o) for o in stored]

    def _register(self, file, n, term, user):
        self.verbruik.register(
            {"bestand": file["mid"], "titel": file["titel"], "pagina": n, "term": term, "model": self.detector.model},
            user=user,
        )

    def _image(self, file, page, context):
        """Page image for the detector, fetched once per request (dummy needs none)."""
        if not self.detector.betaald:
            return None
        if context["image"] is None:
            data = self.client.page_image(file, page["n"], IMAGE_WIDTH)
            context["image"] = Image.open(io.BytesIO(data)).convert("RGB")
        return context["image"]

    def _stamp(self, page, term, stored):
        """A page object from a cached detector object: stable id and search term."""
        obj = dict(stored)
        digest = hashlib.sha1(f"{page['id']}|{obj['herkomst'].get('model')}|{term['en']}|{obj['id']}".encode())
        obj["id"] = "obj-" + digest.hexdigest()[:10]
        obj["zoekterm"] = term["term"]
        obj["label"] = term["en"]
        return obj

    @classmethod
    def _merge_duplicates(cls, objects):
        """New finds that show the same picture count once (the preferred one stays)."""
        return cls._one_per_picture(objects)[0]

    def _commons_objects(self, file, page):
        """Regions that already exist on Commons (7.5): depicts with a position
        and file notes. Free; only for page 1 (positions refer to the image)."""
        if page["n"] != 1:
            return []
        try:
            extracted = self.client.depicted_by_extracted(file)
        except Exception:  # noqa: BLE001 - marking "al uitgesneden" is a nicety
            extracted = set()
        from .. import wikitekst

        return regios.depicts_regions(file, page, file.get("_labels"), extracted) + regios.note_regions(
            file, page, wikitekst.image_notes(file.get("_wikitekst"))
        )

    # -- Click search, box prompt and manual rectangle ----------------------------

    @_locked
    def point(self, file, n, x, y, user=None):
        """The smallest known object under (x, y); otherwise a point prompt."""
        objects = self.page_objects(file, n)
        hits = [o for o in objects if o["status"] != "uitgesloten" and _contains(o["box"], x, y)]
        if hits:
            best = min(hits, key=lambda o: o["box"]["w"] * o["box"]["h"])
            return {"object": self.public(file, n, best), "nieuw": False, "budget": self.verbruik.status(user)}

        page = self.client.load_page(file, n)
        if self.detector.betaald:
            self.verbruik.check(1, user=user, cost=KOSTEN_PER_AFBEELDING)
        detected = self.detector.detect_point(
            self._image(file, page, {"image": None}), x, y, native_size=(page["breedte"], page["hoogte"])
        )
        if self.detector.betaald:
            self._register(file, n, f"punt {int(x)},{int(y)}", user)
        if not detected:
            return {"object": None, "nieuw": False, "budget": self.verbruik.status(user)}
        term = {"term": "klik", "en": f"punt {int(x)},{int(y)}"}
        obj = self._stamp(page, term, detected[0].to_dict())
        obj["label"] = "klik"
        obj["status"] = "kandidaat"
        objects = self._merge_into_page(file, n, [obj])
        result = next((o for o in objects if obj["id"] in _ids(o)), obj)
        return {"object": self.public(file, n, result), "nieuw": result["id"] == obj["id"], "budget": self.verbruik.status(user)}

    @_locked
    def rectangle(self, file, n, box):
        """A manual rectangle (Shift-drag, 7.3): free, without a mask."""
        page = self.client.load_page(file, n)
        box = self._clamp(box, page)
        key = f"{page['id']}|handmatig|{box['x']},{box['y']},{box['w']},{box['h']}"
        obj = {
            "id": "obj-" + hashlib.sha1(key.encode()).hexdigest()[:10],
            "bron": "handmatig",
            "label": "rechthoek",
            "zoekterm": "rechthoek",
            "score": None,
            "box": box,
            "masker": None,
            "status": "geselecteerd",
            "herkomst": {"model": "handmatig", "prompt": None, "tijdstempel": _now()},
        }
        objects = self._merge_into_page(file, n, [obj])
        result = next((o for o in objects if obj["id"] in _ids(o)), obj)
        return {"object": self.public(file, n, result), "nieuw": result["id"] == obj["id"], "budget": self.verbruik.status()}

    @_locked
    def refine_mask(self, file, n, object_id, user=None):
        """The shape of an object with a rectangle (a region from Commons or a
        manual rectangle) via one SAM box prompt (7.5): paid in live mode. The
        object keeps its box and identity; it gets SAM's mask."""
        store = self._load_store(file, n)
        obj = next((o for o in store["objecten"] if o["id"] == object_id), None)
        if obj is None:
            raise DetectionError(f"Object '{object_id}' niet gevonden.", status=404)
        page = self.client.load_page(file, n)
        if self.detector.betaald:
            self.verbruik.check(1, user=user, cost=KOSTEN_PER_AFBEELDING)
        detected = self.detector.detect_box(
            self._image(file, page, {"image": None}), obj["box"], native_size=(page["breedte"], page["hoogte"])
        )
        if self.detector.betaald:
            self._register(file, n, f"box {obj['box']}", user)
        if not detected or not detected[0].mask_data:
            raise DetectionError("SAM vond in deze rechthoek geen object.", status=404, code="no_mask")
        found = detected[0]
        # The mask covers SAM's box; the object keeps its own box, so the mask
        # is only usable when the boxes (nearly) coincide. Otherwise adopt SAM's box.
        obj["masker"] = found.mask_data
        obj["box_regio"] = obj.get("box_regio") or obj["box"]
        obj["box"] = found.box
        obj["masker_herkomst"] = {**found.herkomst, "bron": found.bron}
        self._write_store(file, n, store)
        return {"object": self.public(file, n, obj), "budget": self.verbruik.status(user)}

    @staticmethod
    def _clamp(box, page):
        try:
            x, y, w, h = (float(box[k]) for k in ("x", "y", "w", "h"))
        except (KeyError, TypeError, ValueError):
            raise DetectionError("Geef een rechthoek als {x, y, w, h} in paginapixels.", status=400)
        if w < 0:
            x, w = x + w, -w
        if h < 0:
            y, h = y + h, -h
        x0, y0 = max(0, round(x)), max(0, round(y))
        x1, y1 = min(page["breedte"], round(x + w)), min(page["hoogte"], round(y + h))
        if x1 - x0 < 4 or y1 - y0 < 4:
            raise DetectionError("De rechthoek is te klein.", status=400, code="too_small")
        return {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}

    # -- Page object store ------------------------------------------------------

    def _file_dir(self, file):
        return self.output_dir / file["mid"]

    def _store_path(self, file, n):
        return self._file_dir(file) / f"pagina_{n}" / "objecten.json"

    def _load_store(self, file, n):
        """The page's object store: {"objecten": [...], "prullenbak": [...]}.
        Objects in the trash keep their data and can be restored; while they
        are there, a repeated search does not put them back on the page."""
        path = self._store_path(file, n)
        if path.exists():
            mark_used(path)  # the page's objects count as used (cleanup, 12.1)
        store = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        store.setdefault("objecten", [])
        store.setdefault("prullenbak", [])
        _fill_dutch_names(store)
        return store

    def page_objects(self, file, n):
        return self._load_store(file, n)["objecten"]

    def _write_store(self, file, n, store):
        """Write objecten.json readably. SAM mask payloads (large base85
        strings) go to pagina_<n>/sam/<object-id>.json; the store keeps a
        reference ("bestand"). Also keeps bestand.json, the file's metadata,
        for /objecten and the zip."""
        path = self._store_path(file, n)
        path.parent.mkdir(parents=True, exist_ok=True)
        for obj in store["objecten"] + store["prullenbak"]:
            mask = obj.get("masker")
            if mask and mask.get("payload"):
                relative = f"sam/{obj['id']}.json"
                (path.parent / "sam").mkdir(exist_ok=True)
                (path.parent / relative).write_text(json.dumps(mask, ensure_ascii=False), encoding="utf-8")
                obj["masker"] = {k: v for k, v in mask.items() if k != "payload"} | {"bestand": relative}
        clean = {**store, "objecten": [self._without_display(o) for o in store["objecten"]],
                 "prullenbak": [self._without_display(o) for o in store["prullenbak"]]}
        _write_atomic(path, json.dumps(clean, ensure_ascii=False, indent=2))
        _write_atomic(self._file_dir(file) / "bestand.json", json.dumps(public_file(file), ensure_ascii=False, indent=2))

    @staticmethod
    def _without_display(obj):
        return {k: v for k, v in obj.items() if k != "label_nl"}

    def _mask_data(self, file, n, obj):
        """The complete mask description of an object (payload read back from
        its file under pagina_<n>/sam/ when it was moved out of the store)."""
        mask = obj.get("masker")
        if mask and mask.get("bestand") and not mask.get("payload"):
            path = self._store_path(file, n).parent / mask["bestand"]
            return json.loads(path.read_text(encoding="utf-8"))
        return mask

    def _save(self, file, n, objects):
        store = self._load_store(file, n)
        store["objecten"] = objects
        self._write_store(file, n, store)

    @_locked
    def _merge_into_page(self, file, n, new_objects):
        """Add or update objects; objects in the trash stay there. What the user
        made or paid for (caption, description, Commons concept, a SAM mask on
        a region, the status) is kept. An object showing the same picture as
        one on the page is merged with it, except regions from Commons."""
        store = self._load_store(file, n)
        blocked = {i for o in store["prullenbak"] for i in _ids(o)}
        objects = store["objecten"]
        for obj in new_objects:
            if obj["id"] in blocked:
                continue
            same_id = next((o for o in objects if obj["id"] in _ids(o)), None)
            if same_id is not None and same_id["id"] != obj["id"]:
                continue  # already merged into another object
            if same_id is not None:
                for key in KEPT_ON_UPDATE:
                    if key in same_id and (key != "status" or obj.get("bron") == "commons"):
                        obj[key] = same_id[key]
                if same_id.get("box_regio"):
                    obj["box"], obj["box_regio"] = same_id["box"], same_id["box_regio"]
                objects[objects.index(same_id)] = obj
                continue
            twin = next((o for o in objects if _mergeable(o, obj)), None)
            if twin is None:
                objects.append(obj)
            else:
                objects[objects.index(twin)] = self._absorb(file, n, twin, obj)
        self._write_store(file, n, store)
        return objects

    def _absorb(self, file, n, a, b):
        """Merge two objects showing the same picture into one (see _preference);
        the other is listed under "ook". Status, caption, description and the
        Commons concept of `a` (already on the page) are kept."""
        primary, other = (a, b) if _preference(a) <= _preference(b) else (b, a)
        merged = dict(primary)
        merged["status"] = a["status"]
        for key in ("bijschrift", "commons"):
            if key in a:
                merged[key] = a[key]
        description = a.get("beschrijving") or b.get("beschrijving")
        if description:
            merged["beschrijving"] = description
        merged["ook"] = [e for e in primary.get("ook", []) + other.get("ook", [])] + [_summary(other)]
        if other.get("opgeslagen"):
            self._remove_files(file, other)
        if (other.get("masker") or {}).get("bestand"):
            (self._store_path(file, n).parent / other["masker"]["bestand"]).unlink(missing_ok=True)
        return merged

    @_locked
    def merge_duplicates(self, file, n):
        """Merge objects on a page that show the same picture ("Dubbelingen
        samenvoegen", 7.4). Returns how many objects were merged away."""
        store = self._load_store(file, n)
        # The same grouping as everywhere (_one_per_picture); each duplicate goes into
        # the object that is kept, which keeps its id, status and texts.
        kept, duplicates = self._one_per_picture(store["objecten"])
        by_id = {o["id"]: o for o in store["objecten"]}
        heads = {o["id"]: o for o in kept}
        for duplicate, head in duplicates.items():
            heads[head] = self._absorb(file, n, heads[head], by_id[duplicate])
        merged = list(heads.values())
        count = len(store["objecten"]) - len(merged)
        if count:
            order = {o["id"]: i for i, o in enumerate(store["objecten"])}
            store["objecten"] = sorted(merged, key=lambda o: order.get(o["id"], 0))
            self._write_store(file, n, store)
        return count

    # -- Changing objects ---------------------------------------------------------

    @_locked
    def set_caption(self, file, n, object_id, value):
        """Change an object's caption: {"tekst": ...} sets it, None removes it."""
        store = self._load_store(file, n)
        obj = self._find_in(store, object_id)
        if value is None:
            obj["bijschrift"] = None
        elif isinstance(value, dict) and isinstance(value.get("tekst"), str):
            text = " ".join(value["tekst"].split())
            obj["bijschrift"] = {"tekst": text, "bron": "handmatig"} if text else None
        else:
            raise DetectionError('Geef bijschrift als {"tekst": "..."} of null.', status=400)
        self._write_store(file, n, store)
        return self.public(file, n, obj)

    @_locked
    def set_field(self, file, n, object_id, key, value):
        """Store a field on an object (e.g. the Commons concept) and return it."""
        store = self._load_store(file, n)
        obj = self._find_in(store, object_id)
        obj[key] = value
        self._write_store(file, n, store)
        return self.public(file, n, obj)

    @_locked
    def delete_object(self, file, n, object_id):
        """Move an object to the trash (it can be restored)."""
        store = self._load_store(file, n)
        obj = next((o for o in store["objecten"] if o["id"] == object_id), None)
        if obj is None:
            raise DetectionError(f"Object '{object_id}' niet gevonden.", status=404)
        store["objecten"].remove(obj)
        obj["verwijderd_op"] = _now()
        store["prullenbak"].append(obj)
        self._write_store(file, n, store)
        return [self.public(file, n, o) for o in store["objecten"]]

    @_locked
    def restore_object(self, file, n, object_id):
        """Put an object from the trash back on its page."""
        store = self._load_store(file, n)
        obj = next((o for o in store["prullenbak"] if o["id"] == object_id), None)
        if obj is None:
            raise DetectionError(f"Object '{object_id}' staat niet in de prullenbak.", status=404)
        store["prullenbak"].remove(obj)
        obj.pop("verwijderd_op", None)
        twin = next((o for o in store["objecten"] if _mergeable(o, obj)), None)
        if twin is None:
            store["objecten"].append(obj)
        else:
            store["objecten"][store["objecten"].index(twin)] = self._absorb(file, n, twin, obj)
        self._write_store(file, n, store)
        return [self.public(file, n, o) for o in store["objecten"]]

    @_locked
    def purge_object(self, file, n, object_id):
        """Delete an object permanently, with its saved files."""
        store = self._load_store(file, n)
        before = len(store["objecten"]) + len(store["prullenbak"])
        for obj in store["objecten"] + store["prullenbak"]:
            if obj["id"] != object_id:
                continue
            self._remove_files(file, obj)
            if (obj.get("masker") or {}).get("bestand"):
                (self._store_path(file, n).parent / obj["masker"]["bestand"]).unlink(missing_ok=True)
        store["objecten"] = [o for o in store["objecten"] if o["id"] != object_id]
        store["prullenbak"] = [o for o in store["prullenbak"] if o["id"] != object_id]
        if len(store["objecten"]) + len(store["prullenbak"]) == before:
            raise DetectionError(f"Object '{object_id}' niet gevonden.", status=404)
        self._write_store(file, n, store)
        return [self.public(file, n, o) for o in store["objecten"]]

    def _remove_files(self, file, obj):
        """Delete an object's saved files (a file open elsewhere stays)."""
        for key, value in (obj.pop("opgeslagen", None) or {}).items():
            if key in SAVED_META:
                continue
            try:
                (self._file_dir(file) / value).unlink(missing_ok=True)
            except OSError:
                pass

    @_locked
    def set_selection(self, file, n, ids):
        """Exactly these objects are selected; other selected ones become candidates."""
        if not isinstance(ids or [], list) or not all(isinstance(i, str) for i in ids or []):
            raise DetectionError("'geselecteerd' is een lijst van object-id's.", status=400, code="invalid_body")
        ids = set(ids or [])
        objects = self.page_objects(file, n)
        unknown = ids - {o["id"] for o in objects}
        if unknown:
            raise DetectionError(f"Onbekende object-id's: {', '.join(sorted(unknown))}.", status=404)
        for obj in objects:
            if obj["id"] in ids:
                obj["status"] = "geselecteerd"
            elif obj["status"] == "geselecteerd":
                obj["status"] = "kandidaat"
        self._save(file, n, objects)
        return [self.public(file, n, o) for o in objects]

    @_locked
    def set_statuses(self, file, n, changes):
        """Set the status of objects: [{"id", "status"}, ...]."""
        objects = self.page_objects(file, n)
        by_id = {o["id"]: o for o in objects}
        for change in changes:
            if not isinstance(change, dict) or not isinstance(change.get("id"), str) or change.get("status") not in STATUSES:
                raise DetectionError(f"Elke wijziging is {{\"id\", \"status\"}} met status {', '.join(STATUSES)}.", status=400)
            if change.get("id") not in by_id:
                raise DetectionError(f"Onbekend object: {change.get('id')}.", status=404)
        for change in changes:
            by_id[change["id"]]["status"] = change["status"]
        self._save(file, n, objects)
        return [self.public(file, n, o) for o in objects]

    # -- Saving (functional design 9.5: full resolution) ---------------------------

    @staticmethod
    def _one_per_picture(objects):
        """(kept, {duplicate id: kept id}): objects that show the same picture
        count once. Regions from Commons are always kept, each on its own."""
        groups = []
        for obj in sorted(objects, key=_preference):
            group = next((g for g in groups if any(_mergeable(obj, m) for m in g)), None)
            if group:
                group.append(obj)
            else:
                groups.append([obj])
        duplicates = {m["id"]: g[0]["id"] for g in groups for m in g[1:]}
        return [g[0] for g in groups], duplicates

    @_locked
    def save_objects(self, file, n, ids=None):
        """Write cut-outs for the given objects (default: the selected ones),
        from the original at full resolution: a JPG (the rectangle, quality
        95), and for objects with a mask a transparent PNG and the mask, under
        uitvoer/<M-id>/pagina_<n>/."""
        store = self._load_store(file, n)
        wanted = set(ids or [])
        chosen = [o for o in store["objecten"] if (o["id"] in wanted if wanted else o["status"] == "geselecteerd")]
        if not chosen:
            raise DetectionError("Er is niets om op te slaan: selecteer eerst een of meer objecten.", status=400, code="nothing_selected")
        targets, duplicates = self._one_per_picture(chosen)
        page = self.client.load_page(file, n)
        image = self.client.original_image(file, n)
        scale = image.width / page["breedte"]
        folder = self._file_dir(file) / f"pagina_{n}"
        for sub in ("png", "maskers", "jpg"):
            (folder / sub).mkdir(parents=True, exist_ok=True)
        now = _now()
        for obj in targets:
            self._remove_files(file, obj)
            files = {"jpg": f"pagina_{n}/jpg/{obj['id']}.jpg"}
            (folder.parent / files["jpg"]).write_bytes(export.crop_jpeg(image, obj["box"], scale))
            mask_data = self._mask_data(file, n, obj)
            if mask_data:
                png, mask = export.cutout(image, obj["box"], scale, decode_raster(mask_data))
                files["png"] = f"pagina_{n}/png/{obj['id']}.png"
                files["masker"] = f"pagina_{n}/maskers/{obj['id']}_mask.png"
                (folder.parent / files["png"]).write_bytes(png)
                (folder.parent / files["masker"]).write_bytes(mask)
            x0, y0, x1, y1 = export._rect(obj["box"], scale)
            obj["opgeslagen"] = {**files, "tijdstempel": now, "breedte": x1 - x0, "hoogte": y1 - y0}
        self._write_store(file, n, store)
        return {
            "opgeslagen": [o["id"] for o in targets],
            "dubbel": duplicates,
            "map": str(folder),
            "objecten": [self.public(file, n, o) for o in store["objecten"]],
        }

    def saved_file(self, file, n, object_id, kind):
        """Bytes of a saved cut-out ("jpg" or "png") at full resolution; made
        on the fly (not stored) when the object was not saved yet."""
        obj = self._find(file, n, object_id)
        path = (obj.get("opgeslagen") or {}).get(kind)
        if path and (self._file_dir(file) / path).exists():
            mark_used(self._file_dir(file) / path)
            return (self._file_dir(file) / path).read_bytes()
        page = self.client.load_page(file, n)
        image = self.client.original_image(file, n)
        scale = image.width / page["breedte"]
        if kind == "jpg":
            return export.crop_jpeg(image, obj["box"], scale)
        return export.cutout(image, obj["box"], scale, decode_raster(self._mask_data(file, n, obj)))[0]

    def file_facts(self, file, n, obj, kind):
        """Size in bytes, SHA-1 and width and height in pixels of the cut-out
        file in format `kind` ("jpg" or "png"), as it would be uploaded: the
        saved file, else made on the fly. Remembered per box, mask and format,
        so the concept does not make the file again on every change."""
        key = json.dumps([file["mid"], n, obj["id"], obj["box"], obj.get("masker"), obj.get("opgeslagen"), kind], sort_keys=True)
        if key not in self._facts:
            data = self.saved_file(file, n, obj["id"], kind)
            width, height = Image.open(io.BytesIO(data)).size
            if len(self._facts) > 500:
                self._facts.clear()
            self._facts[key] = {"sha1": hashlib.sha1(data).hexdigest(), "bytes": len(data), "breedte": width, "hoogte": height}
        return self._facts[key]

    @_locked
    def empty_trash(self, targets=None):
        """Permanently delete objects in the trash: all of them, or only the
        given {"mid", "pagina", "id"} entries. Returns how many were deleted."""
        try:
            wanted = {(str(t["mid"]), int(t["pagina"]), str(t["id"])) for t in targets} if targets is not None else None
        except (KeyError, TypeError, ValueError):
            raise DetectionError("Elk object is {\"mid\", \"pagina\", \"id\"}.", status=400, code="invalid_body") from None
        deleted = 0
        for entry in self.all_objects(trash=True):
            key = (entry["mid"], entry["pagina"], entry["id"])
            if wanted is not None and key not in wanted:
                continue
            self.purge_object({"mid": entry["mid"]}, entry["pagina"], entry["id"])
            deleted += 1
        return deleted

    def _find(self, file, n, object_id):
        return self._find_in(self._load_store(file, n), object_id)

    @staticmethod
    def _find_in(store, object_id):
        obj = next((o for o in store["objecten"] + store["prullenbak"] if o["id"] == object_id), None)
        if obj is None:
            raise DetectionError(f"Object '{object_id}' niet gevonden.", status=404)
        return obj

    def cutout_jpeg(self, file, n, object_id, width=300):
        """Preview of an object: the box without mask, scaled to `width`
        (None: full resolution), cached on disk. Small previews come from a
        reduced page image, large ones from the original."""
        obj = self._find(file, n, object_id)
        box = obj["box"]
        key = hashlib.sha1(f"{file['sha1']}|{n}|{object_id}|{box}|{width}".encode()).hexdigest()
        path = self.cache_dir.parent / "uitsneden" / key[:2] / f"{key}.jpg"
        if path.exists():
            mark_used(path)
            return path.read_bytes()
        page = self.client.load_page(file, n)
        if width and width <= 400:
            needed = width * page["breedte"] / max(1, box["w"])
            image = Image.open(io.BytesIO(self.client.page_image(file, n, min(needed, page["breedte"]))))
        else:
            image = self.client.original_image(file, n)
        scale = image.width / page["breedte"]
        crop = image.crop(
            (
                int(box["x"] * scale),
                int(box["y"] * scale),
                max(int(box["x"] * scale) + 1, round((box["x"] + box["w"]) * scale)),
                max(int(box["y"] * scale) + 1, round((box["y"] + box["h"]) * scale)),
            )
        )
        crop = crop.convert("RGB")  # the piece only: a large original is never converted as a whole
        if width and crop.width > width:
            crop = crop.resize((width, max(1, round(crop.height * width / crop.width))))
        buffer = io.BytesIO()
        crop.save(buffer, format="JPEG", quality=85)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(buffer.getvalue())
        return buffer.getvalue()

    def all_objects(self, sources=None, trash=False, mid=None, saved=None):
        """Every object on every page in the output folder (or, with `trash`,
        in the trash), newest first, with the file's title and licence (from
        its bestand.json). `mid` limits it to one file; `saved` to saved ones."""
        result = []
        for meta_path in self.output_dir.glob("M*/bestand.json"):
            try:
                file = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if mid and file.get("mid") != mid:
                continue
            for store_path in meta_path.parent.glob("pagina_*/objecten.json"):
                try:
                    n = int(store_path.parent.name.split("_", 1)[1])
                    store = json.loads(store_path.read_text(encoding="utf-8"))
                    store.setdefault("prullenbak", [])
                    _fill_dutch_names(store)
                    objects = store["prullenbak"] if trash else store["objecten"]
                except (OSError, ValueError, KeyError, IndexError):
                    continue
                for obj in objects:
                    if sources and not set(_sources(obj)) & set(sources):
                        continue
                    if saved is not None and bool(obj.get("opgeslagen")) != saved:
                        continue
                    entry = self.public(file, n, obj)
                    entry.update(
                        {
                            "mid": file["mid"],
                            "bestand_titel": file.get("titel"),
                            "bestand_url": file.get("url"),
                            "licentie": (file.get("licentie") or {}).get("kort"),
                            "pagina": n,
                            "app_url": f"/?mid={file['mid']}&pagina={n}&object={obj['id']}",
                        }
                    )
                    result.append(entry)
        key = (lambda o: o.get("verwijderd_op") or "") if trash else (lambda o: (o.get("herkomst") or {}).get("tijdstempel") or "")
        result.sort(key=key, reverse=True)
        return result

    def get_object(self, file, n, object_id):
        """One object (on the page or in the trash), as the API shows it."""
        store = self._load_store(file, n)
        public = self.public(file, n, self._find_in(store, object_id))
        public["in_prullenbak"] = any(o["id"] == object_id for o in store["prullenbak"])
        return public

    def in_trash(self, file, n, object_id):
        return any(o["id"] == object_id for o in self._load_store(file, n)["prullenbak"])

    def mask_png(self, file, n, object_id):
        return self.masks.png(self._mask_data(file, n, self._find(file, n, object_id)))

    # -- Output -------------------------------------------------------------------

    def public(self, file, n, obj):
        """API representation: the mask without its (large) payload, plus URLs;
        for a saved cut-out also when its files go (retention, 12.1)."""
        mask = obj.get("masker")
        public = {k: v for k, v in obj.items() if k != "masker"}
        public["masker"] = (
            {"breedte": mask["width"], "hoogte": mask["height"], "codering": mask["encoding"]} if mask else None
        )
        base = f"/api/v1/bestand/{file['mid']}/pagina/{n}/objecten/{obj['id']}"
        public["bronnen"] = _sources(obj)
        public["label_nl"] = obj.get("label_nl") or (obj["label"] if obj.get("bron") == "commons" else prompts.dutch(obj.get("label")))
        public["masker_url"] = f"{base}/masker.png"
        public["uitsnede_url"] = f"{base}/uitsnede.jpg"
        public["uitsnede_png_url"] = f"{base}/uitsnede.png"
        if obj.get("opgeslagen"):
            public["opgeslagen"] = {**obj["opgeslagen"], **self._expiry(file, obj["opgeslagen"])}
        return public

    def _expiry(self, file, saved):
        """When the saved files of a cut-out are removed: BEWAAR_UITSNEDEN_DAGEN
        after their last use (the cleanup, cutter/opruimen.py). {} when unknown."""
        paths = [self._file_dir(file) / saved[k] for k in ("jpg", "png", "masker") if saved.get(k)]
        present = [p for p in paths if p.exists()]
        if not present:
            return {}
        last = max(last_used(p) for p in present)
        expires = datetime.fromtimestamp(last + self.keep_cutout_days * 86400, timezone.utc)
        return {"laatst_gebruikt": datetime.fromtimestamp(last, timezone.utc).isoformat(timespec="seconds"), "verloopt": expires.isoformat(timespec="seconds")}


def make_detector(config):
    """DummyDetector or MetaSamDetector, by DETECTIE_MODUS."""
    if config["DETECTIE_MODUS"] == "live":
        from .meta_sam import MetaSamDetector

        return MetaSamDetector(
            config["MODEL_API_KEY"], base_url=config["META_API_BASE"], model=config["SAM_MODEL"], max_width=IMAGE_WIDTH
        )
    from .dummy import DummyDetector

    return DummyDetector()


__all__ = ["DetectionService", "make_detector", "iou", "STATUSES", "MODES"]
