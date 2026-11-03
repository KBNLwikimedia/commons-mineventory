"""Structured data on Commons (SDC): reading the MediaInfo entity of a file
(functional design 5.2 and 7.5). Writing SDC for a cut-out is in concept.py.
"""

PUBLIC_DOMAIN = "Q19652"  # P6216 copyright status: public domain

PROPERTIES = {
    "P180": "beeldt_af",
    "P6216": "auteursrechtstatus",
    "P275": "licentie",
    "P170": "maker",
    "P571": "datum",
    "P195": "collectie",
    "P7482": "bron",
}


def _value(snak):
    """A snak's value as a plain string or Q-id, with its kind. `somevalue`
    (e.g. an unknown maker) becomes None with kind "onbekend"."""
    if snak.get("snaktype") != "value":
        return None, "onbekend" if snak.get("snaktype") == "somevalue" else "geen"
    data = snak.get("datavalue") or {}
    value, kind = data.get("value"), data.get("type")
    if kind == "wikibase-entityid":
        return value.get("id") or f"Q{value.get('numeric-id')}", "item"
    if kind == "time":
        return value.get("time"), "tijd"
    if kind == "monolingualtext":
        return value.get("text"), "tekst"
    if kind == "quantity":
        return value.get("amount"), "hoeveelheid"
    return value, "tekst"


def _qualifiers(statement):
    result = {}
    for prop, snaks in (statement.get("qualifiers") or {}).items():
        result[prop] = [_value(s)[0] for s in snaks]
    return result


def parse_entity(entity):
    """Captions and the statements the app uses, from a wbgetentities entity.

    Returns {"mid", "captions": {lang: text}, "beeldt_af": [...], "auteursrechtstatus":
    [...], …}; every statement is {"verklaring": id, "waarde", "soort", "kwalificatoren"}.
    """
    entity = entity or {}
    result = {
        "mid": entity.get("id"),
        "bestaat": "missing" not in entity and bool(entity.get("id")),
        "captions": {lang: label.get("value") for lang, label in (entity.get("labels") or {}).items()},
    }
    statements = entity.get("statements") or entity.get("claims") or {}
    if isinstance(statements, list):  # an entity without statements serialises as []
        statements = {}
    for prop, key in PROPERTIES.items():
        result[key] = []
        for statement in statements.get(prop, []):
            value, kind = _value(statement.get("mainsnak") or {})
            result[key].append(
                {
                    "verklaring": statement.get("id"),
                    "eigenschap": prop,
                    "waarde": value,
                    "soort": kind,
                    "kwalificatoren": _qualifiers(statement),
                    "rang": statement.get("rank", "normal"),
                    "_mainsnak": statement.get("mainsnak"),
                    "_qualifiers": statement.get("qualifiers"),
                }
            )
    return result


def item_ids(parsed):
    """All Q-ids in the parsed entity (for one labels lookup on Wikidata)."""
    ids = []
    for key in PROPERTIES.values():
        for statement in parsed.get(key, []):
            if statement["soort"] == "item":
                ids.append(statement["waarde"])
            for values in statement["kwalificatoren"].values():
                ids += [v for v in values if isinstance(v, str) and v.startswith("Q") and v[1:].isdigit()]
    return list(dict.fromkeys(ids))


def is_public_domain(parsed):
    return any(s["waarde"] == PUBLIC_DOMAIN for s in parsed.get("auteursrechtstatus", []))


def summary(parsed, labels=None):
    """What the UI shows of the SDC: captions and each statement's value with
    its label (nl, else en, else the Q-id). Depicts keeps its position (P2677)."""
    labels = labels or {}

    def label(value):
        return labels.get(value) or {"nl": None, "en": None}

    result = {"captions": parsed.get("captions", {})}
    for key in PROPERTIES.values():
        result[key] = [
            {
                "waarde": s["waarde"],
                "soort": s["soort"],
                "label": (label(s["waarde"]).get("nl") or label(s["waarde"]).get("en") or s["waarde"]) if s["soort"] == "item" else s["waarde"],
                "label_en": label(s["waarde"]).get("en") if s["soort"] == "item" else None,
                **({"positie": (s["kwalificatoren"].get("P2677") or [None])[0]} if key == "beeldt_af" else {}),
            }
            for s in parsed.get(key, [])
        ]
    return result
