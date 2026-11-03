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
FORBIDDEN = re.compile(r"[#<>\[\]{}|/\\:\x00-\x1f\x7f]")
TRACKING_CATEGORY = "Uploaded with Commons Cutter"
UPLOAD_SUMMARY = (
    "Uitsnede uit [[{original}]] met de [[Commons:Commons Cutter|Commons Cutter]]; beschrijving deels "
    "opgesteld met een taalmodel en gecontroleerd door de uploader."
)
# Fields of {{Artwork}}, {{Photograph}} and {{Book}} that also hold for a cut-out (9.3).
KEPT_FIELDS = (
    "artist", "author", "photographer", "illustrator", "date", "medium", "institution",
    "accession number", "credit line", "object history", "references", "permission",
)
# Statements copied from the original (9.4).
COPIED_PROPERTIES = ("P6216", "P275", "P170", "P571", "P195")
FORMATS = ("jpg", "png")
EDITABLE = {
    "bestandsnaam", "formaat", "beschrijving", "caption", "datum", "maker", "categorieen",
    "beeldt_af", "image_extracted", "merk_bevestigd", "gekozen",
}


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


def default_concept(file, obj):
    """The proposal for an object, from the original and the object (free)."""
    text = file.get("_wikitekst") or ""
    info = wikitekst.info_template(text)
    params = info.params if info else {}
    description = obj.get("beschrijving") or {}
    label_nl = obj.get("label_nl") or obj.get("label")
    caption = obj.get("bijschrift") or {}
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
        "datum": params.get("date", ""),
        "maker": params.get("author") or params.get("artist") or params.get("photographer") or "",
        "permissie": params.get("permission", ""),
        "licentie": wikitekst.license_templates(text),
        "categorieen": [{"naam": c, "gekozen": True} for c in file.get("categorieen", [])],
        "beeldt_af": depicts,
        "image_extracted": True,
        "merk_bevestigd": None,
        "gekozen": None,
    }


def concept(file, obj):
    """The concept of an object: the proposal with the user's changes
    (`obj["commons"]`) on top, plus the derived rights label, wikitext and SDC."""
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
    result["sdc"] = structured_data(file, result)
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
    for key in ("beschrijving", "caption"):
        if key in body:
            value = body[key]
            if not isinstance(value, dict) or not all(isinstance(v, str) for v in value.values()):
                raise ValueError(f"'{key}' is een object met teksten per taal, bijv. {{\"nl\": \"…\", \"en\": \"…\"}}.")
            if key == "caption" and any(len(v) > MAX_CAPTION for v in value.values()):
                raise ValueError(f"Een caption is hooguit {MAX_CAPTION} tekens.")
    if "categorieen" in body and not (
        isinstance(body["categorieen"], list) and all(isinstance(c, dict) and isinstance(c.get("naam"), str) for c in body["categorieen"])
    ):
        raise ValueError("'categorieen' is een lijst van {\"naam\": …, \"gekozen\": true|false}.")
    if "beeldt_af" in body and not (
        isinstance(body["beeldt_af"], list) and all(isinstance(d, dict) and re.fullmatch(r"Q\d+", str(d.get("q", ""))) for d in body["beeldt_af"])
    ):
        raise ValueError("'beeldt_af' is een lijst van {\"q\": \"Q…\", \"label\": …}.")
    for key in ("image_extracted",):
        if key in body and not isinstance(body[key], bool):
            raise ValueError(f"'{key}' is true of false.")
    if "merk_bevestigd" in body and body["merk_bevestigd"] is not None and not (
        isinstance(body["merk_bevestigd"], str) and body["merk_bevestigd"].strip()
    ):
        raise ValueError("'merk_bevestigd' is een reden (tekst), of null.")
    return body


# -- Wikitext (9.3) ---------------------------------------------------------------------


def _languages(texts):
    return "".join(f"{{{{{lang}|1={text.strip()}}}}}" for lang, text in texts.items() if text and text.strip())


def wikitext(file, c):
    """The wikitext of the new file page. {{Extracted from}} is always there
    and cannot be removed (Olaf, 3-11-2026)."""
    original = file["titel"]
    info = wikitekst.info_template(file.get("_wikitekst") or "")
    description = _languages({"nl": c["beschrijving"].get("nl", ""), "en": c["beschrijving"].get("en", "")})
    source = f"{{{{Extracted from|{original}}}}}"
    if info and info.name in ("artwork", "photograph", "book"):
        name = {"artwork": "Artwork", "photograph": "Photograph", "book": "Book"}[info.name]
        fields = [f"|{key}={info.params[key]}" for key in KEPT_FIELDS if info.params.get(key) and key not in ("date", "permission")]
        fields += [
            f"|title={_languages({'nl': c['caption'].get('nl', ''), 'en': c['caption'].get('en', '')})}",
            f"|description={description}",
            f"|date={c['datum']}",
            f"|source={source}",
            f"|permission={c.get('permissie', '')}",
            "|other versions=",
        ]
        info_text = "{{" + name + "\n" + "\n".join(fields) + "\n}}"
    else:
        info_text = "\n".join(
            [
                "{{Information",
                f"|description={description}",
                f"|date={c['datum']}",
                f"|source={source}",
                f"|author={c['maker']}",
                f"|permission={c.get('permissie', '')}",
                "|other versions=",
                "}}",
            ]
        )
    licence = "\n".join(c["licentie"]) or "<!-- Geen licentiesjabloon gevonden op het origineel: vul dit aan. -->"
    if any(n in (file.get("_wikitekst") or "").lower() for n in ("{{flickrreview", "{{licensereview")):
        licence += f"\n<!-- De licentiecontrole van het origineel geldt ook hier; zie [[:{original}]]. -->"
    categories = [cat["naam"] for cat in c["categorieen"] if cat.get("gekozen") and cat.get("naam")]
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


def structured_data(file, c):
    """What one wbeditentity on the new M-id would set (9.4): captions, depicts
    (the chosen items, without a position) and the statements copied from the
    original. The relation to the original stays in the wikitext for now."""
    labels = {lang: {"language": lang, "value": text[:MAX_CAPTION]} for lang, text in c["caption"].items() if text}
    claims = []
    for depicted in c["beeldt_af"]:
        claims.append({"mainsnak": _item_snak("P180", depicted["q"]), "type": "statement", "rank": "normal"})
    parsed = file.get("_sdc") or {}
    from .sdc import PROPERTIES

    for prop in COPIED_PROPERTIES:
        for statement in parsed.get(PROPERTIES[prop], []):
            if not statement.get("_mainsnak"):
                continue
            claim = {"mainsnak": statement["_mainsnak"], "type": "statement", "rank": statement.get("rang", "normal")}
            if statement.get("_qualifiers"):
                claim["qualifiers"] = statement["_qualifiers"]
            claims.append(claim)
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
            warnings.append({"code": "exists", "tekst": f"Er bestaat al een bestand met de naam '{name}'."})
        if taken[name] > 1:
            warnings.append({"code": "duplicate_name", "tekst": "Twee uitsneden hebben dezelfde naam; geef er een een volgnummer."})
        if duplicates:
            warnings.append({"code": "duplicate", "tekst": "Dezelfde afbeelding staat al op Commons: " + ", ".join(duplicates) + "."})
        if missing:
            warnings.append({"code": "missing_category", "tekst": "Deze categorieën bestaan niet: " + ", ".join(missing) + "."})
        if not c["upload_toegestaan"]:
            warnings.append({"code": "not_allowed", "tekst": "Uploaden is voor deze uitsnede uitgeschakeld (rechtenlabel)."})
        result[oid] = {
            "bestandsnaam": c["bestandsnaam"],
            "naam_bestaat": bool(existing_names.get(name)),
            "dubbel_op_commons": duplicates,
            "ontbrekende_categorieen": missing,
            "waarschuwingen": warnings,
            "in_orde": not warnings,
        }
    return result
