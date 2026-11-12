"""Depicts and captions for the whole image (functional design 9.7, backlog 15b).

What the window "Gegevens van deze afbeelding" needs: what the file already has
on Commons (captions, depicts with or without a position), the proposals from
this app (items chosen for cut-outs, the AI search terms of the page overview,
the Wikidata suggestions of "Wat staat hierop?"), the AI caption, and the
user's choices so far (a draft). Free: nothing is asked of a model, and
nothing changes on Commons. Saving to Commons comes in phase 2.

The AI search terms are not looked up on Wikidata here: the window does that
per term (GET /wikidata/zoek, cached), so the window opens at once.
"""

import json
import re
from datetime import datetime, timezone

from .detectie.basis import DetectionError

CAPTION_MAX = 250
LANGUAGES = ("nl", "en")
CHOICES = ("toevoegen", "houden", "vervangen", "zelf")


def _position(obj, page):
    """P2677 of an object in the whole image ("pct:x,y,w,h"), as for a cut-out (9.4)."""
    box, width, height = obj["box"], page["breedte"], page["hoogte"]
    pct = [box["x"] / width * 100, box["y"] / height * 100, box["w"] / width * 100, box["h"] / height * 100]
    return "pct:" + ",".join(f"{round(v, 4):g}" for v in pct)


def _object_items(obj):
    """The depicts items of an object: its Commons concept, else the item it was found for."""
    stored = (obj.get("commons") or {}).get("beeldt_af")
    if stored:
        return [{"q": d["q"], "label": d.get("label") or d["q"]} for d in stored if d.get("q")]
    if obj.get("wikidata"):
        return [{"q": obj["wikidata"], "label": obj.get("label_item") or obj.get("label_nl") or obj.get("label") or obj["wikidata"]}]
    return []


def draft_path(service, file, n):
    return service._file_dir(file) / f"pagina_{n}" / "origineel.json"


def gather(service, file, n):
    """Everything the window shows, from what is stored (no model, no edit)."""
    page = service.client.load_page(file, n)
    store = service._load_store(file, n)
    objects = [o for o in store["objecten"] if o.get("status") != "uitgesloten"]
    sdc = file.get("sdc") or {}
    single = file.get("paginas", 1) == 1

    def short(obj):
        # "upload": the cut-out is saved, so its upload would put this region on the original
        # too (9.4); the window then does not add a second statement for it (rule 4).
        return {"id": obj["id"], "positie": _position(obj, page) if single else None, "naam": obj.get("naam") or obj.get("label_nl") or obj.get("label"), "upload": bool(obj.get("opgeslagen"))}

    chosen = {}
    for obj in objects:
        for item in _object_items(obj):
            row = chosen.setdefault(item["q"], {"q": item["q"], "label": item["label"], "objecten": []})
            row["objecten"].append(short(obj))

    overview = store.get("inventaris") or {}
    terms = []
    for term in overview.get("zoektermen") or []:
        en = term.get("en") or ""
        members = [short(o) for o in objects if (o.get("zoekterm") or "").lower() == en.lower() and o.get("bron") != "groep"]
        terms.append({"en": en, "nl": term.get("nl") or en, "objecten": members})

    suggestions = {}
    for obj in objects:
        for text in (obj.get("beschrijving") or {}).get("wikidata_suggesties") or []:
            key = str(text).strip()
            if key:
                suggestions.setdefault(key.lower(), {"term": key, "objecten": []})["objecten"].append(short(obj))

    path = draft_path(service, file, n)
    draft = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return {
        "mid": file["mid"],
        "titel": file.get("titel"),
        "pagina": n,
        "meerdere_paginas": not single,
        "revisie": file.get("revisie"),
        "op_commons": {
            "captions": sdc.get("captions") or {},
            "beeldt_af": [
                {"q": s["waarde"], "label": s.get("label"), "label_en": s.get("label_en"), "positie": s.get("positie")}
                for s in sdc.get("beeldt_af") or [] if s.get("soort") == "item"
            ],
        },
        "gekozen": list(chosen.values()),
        "zoektermen": terms,
        "suggesties": list(suggestions.values()),
        "ai_caption": _ai_caption(overview),
        "concept": draft,
    }


def _ai_caption(overview):
    """The description of the image for a caption: the Commons caption length when it was
    made (all four lengths come at once since 0.39.0, with hand edits), else what is shown."""
    caption = (overview.get("beschrijvingen") or {}).get("caption")
    if caption and overview.get("beschrijvingsniveau") != "caption":
        return {"nl": caption.get("nl") or "", "en": caption.get("en") or "", "beschrijvingsniveau": "caption"}
    return {
        "nl": overview.get("samenvatting") or "",
        "en": overview.get("samenvatting_en") or "",
        "beschrijvingsniveau": overview.get("beschrijvingsniveau") or ("normaal" if overview.get("samenvatting") else None),
    }


def _invalid(message):
    return DetectionError(message, status=400, code="invalid_body")


def save_draft(service, file, n, body):
    """Keep the user's choices (a draft; nothing goes to Commons). Checked, then
    written to uitvoer/<mid>/pagina_<n>/origineel.json."""
    if not isinstance(body, dict):
        raise _invalid("Geef een object met 'beeldt_af' en 'captions'.")
    depicts = body.get("beeldt_af", [])
    if not isinstance(depicts, list):
        raise _invalid("'beeldt_af' is een lijst.")
    clean_depicts = []
    for entry in depicts:
        if not isinstance(entry, dict) or not re.fullmatch(r"Q\d+", str(entry.get("q", ""))):
            raise _invalid("Elk 'beeldt_af' heeft een 'q' (Q-id).")
        objects = entry.get("objecten", [])
        if not isinstance(objects, list) or not all(isinstance(o, str) for o in objects):
            raise _invalid("'objecten' is een lijst van object-id's.")
        clean_depicts.append({
            "q": entry["q"],
            "label": str(entry.get("label") or entry["q"])[:200],
            "met_positie": bool(entry.get("met_positie", True)),
            "objecten": objects,
            "bron": str(entry.get("bron") or "")[:40],
            "term": str(entry.get("term") or "")[:100] or None,
        })
    add_position = body.get("positie_bij_bestaande", [])
    if not isinstance(add_position, list) or not all(re.fullmatch(r"Q\d+", str(q)) for q in add_position):
        raise _invalid("'positie_bij_bestaande' is een lijst van Q-id's.")
    hidden = body.get("verborgen", [])
    if not isinstance(hidden, list) or not all(re.fullmatch(r"Q\d+", str(q)) for q in hidden):
        raise _invalid("'verborgen' is een lijst van Q-id's.")
    captions = body.get("captions", {})
    if not isinstance(captions, dict):
        raise _invalid("'captions' is een object per taal.")
    clean_captions = {}
    for lang, caption in captions.items():
        if lang not in LANGUAGES or not isinstance(caption, dict):
            raise _invalid(f"Captions in {', '.join(LANGUAGES)}.")
        choice = caption.get("keuze")
        if choice not in CHOICES:
            raise _invalid(f"'keuze' is een van {', '.join(CHOICES)}.")
        text = " ".join(str(caption.get("tekst") or "").split())
        if len(text) > CAPTION_MAX:
            raise _invalid(f"Een caption is hooguit {CAPTION_MAX} tekens ({lang}: {len(text)}).")
        clean_captions[lang] = {"keuze": choice, "tekst": text}
    draft = {
        "beeldt_af": clean_depicts,
        "positie_bij_bestaande": add_position,
        "verborgen": list(dict.fromkeys(hidden)),  # rows you do not want to see (the bin)
        "captions": clean_captions,
        "bewaard_op": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    path = draft_path(service, file, n)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    return draft


def items_in_draft(service, file, n, object_id):
    """The depicts items the window's draft has for this object (rule 1 of 9.7: one list of
    planned changes per original), to show them in the object's Commons concept."""
    path = draft_path(service, file, n)
    if not path.exists():
        return []
    draft = json.loads(path.read_text(encoding="utf-8"))
    return [e["q"] for e in draft.get("beeldt_af", []) if object_id in (e.get("objecten") or [])]
