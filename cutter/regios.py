"""Regions that already exist on Commons, as free objects (functional design 7.5):

- depicts (P180) statements with a relative position (P2677), the yellow
  rectangles on the file page: `pct:x,y,w,h` (percentages) or `x,y,w,h`
  (pixels, as in IIIF);
- file notes ({{ImageNote}}) in the wikitext.

Each region is an object of its own (source "commons"); regions are never
merged with each other or with other objects.
"""

import hashlib
import math
import re
from datetime import datetime, timezone

from . import __version__

_REGION = re.compile(r"^\s*(pct:)?\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*$", re.IGNORECASE)


def parse_region(value, width, height):
    """A P2677 value as a box in pixels of a width × height image, clamped to
    the image; None when unreadable or empty."""
    match = _REGION.match(value or "")
    if not match:
        return None
    pct, *numbers = match.groups()
    try:
        x, y, w, h = (float(n) for n in numbers)  # "1.2.3" matches the pattern but is no number
    except ValueError:
        return None
    if not all(math.isfinite(v) for v in (x, y, w, h)):
        return None
    if pct:
        x, y, w, h = x * width / 100, y * height / 100, w * width / 100, h * height / 100
    x0, y0 = max(0, round(x)), max(0, round(y))
    x1, y1 = min(width, round(x + w)), min(height, round(y + h))
    if x1 - x0 < 1 or y1 - y0 < 1:
        return None
    return {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}


def _object_id(mid, key):
    return "obj-" + hashlib.sha1(f"{mid}|commons|{key}".encode()).hexdigest()[:10]


def depicts_regions(file, page, labels=None, extracted_items=()):
    """Objects for the P180 statements with P2677 on the file (page 1 only)."""
    labels = labels or {}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    objects = []
    for statement in (file.get("_sdc") or {}).get("beeldt_af", []):
        positions = statement["kwalificatoren"].get("P2677") or []
        for index, position in enumerate(positions):
            box = parse_region(position, page["breedte"], page["hoogte"])
            if box is None:
                continue
            q = statement["waarde"] if statement["soort"] == "item" else None
            names = labels.get(q) or {}
            objects.append(
                {
                    "id": _object_id(file["mid"], f"{statement['verklaring']}|{index}"),
                    "bron": "commons",
                    "soort": "regio",
                    "label": names.get("nl") or names.get("en") or q or "regio",
                    "label_en": names.get("en") or names.get("nl") or q,
                    "zoekterm": "regio",
                    "wikidata": q,
                    "score": None,
                    "box": box,
                    "masker": None,
                    "al_uitgesneden": bool(q and q in extracted_items),
                    "herkomst": {
                        "model": "commons",
                        "prompt": None,
                        "mid": file["mid"],
                        "verklaring": statement["verklaring"],
                        "p2677": position,
                        "tijdstempel": now,
                        "appversie": __version__,
                    },
                }
            )
    return objects


def note_regions(file, page, notes):
    """Objects for the file notes ({{ImageNote}}); their text becomes the caption."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    objects = []
    for note in notes:
        fx, fy = page["breedte"] / note["dimx"], page["hoogte"] / note["dimy"]
        x0, y0 = max(0, round(note["x"] * fx)), max(0, round(note["y"] * fy))
        x1 = min(page["breedte"], round((note["x"] + note["w"]) * fx))
        y1 = min(page["hoogte"], round((note["y"] + note["h"]) * fy))
        if x1 - x0 < 1 or y1 - y0 < 1:
            continue
        text = note["tekst"]
        objects.append(
            {
                "id": _object_id(file["mid"], f"note|{note['id']}"),
                "bron": "commons",
                "soort": "notitie",
                "label": (text[:60] + "…") if len(text) > 60 else (text or "notitie"),
                "label_en": None,
                "zoekterm": "notitie",
                "wikidata": None,
                "score": None,
                "box": {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0},
                "masker": None,
                "bijschrift": {"tekst": text, "bron": "imagenote"} if text else None,
                "herkomst": {"model": "commons", "prompt": None, "mid": file["mid"], "notitie": note["id"], "tijdstempel": now, "appversie": __version__},
            }
        )
    return objects
