"""Prompt parser for the EN/MIN (AND/NOT) operators, the NL->EN term table and
the Snel zoeken groups (functional design 7.1, 7.2 and 7.4; taken over from
the Delpher Uitsnijder).

SAM understands one concept per call, so a prompt becomes a list of terms to
include and a list of terms to exclude; the app combines the results itself.
"""

import re

# Operators, case-insensitive. "-" only counts as an operator before a term
# (start of the prompt or after a space), so "zwart-wit" stays one term.
_OPERATOR = re.compile(
    r"\s+(en|and|min|not)\s+|\s*[,+]\s*|(?:^|\s+)-\s*",
    re.IGNORECASE,
)
_EXCLUDE = {"min", "not"}

# Dutch terms to English noun phrases, which SAM handles more reliably.
# Unknown terms are passed on unchanged (assumed to be English already).
VERTAALTABEL = {
    "advertentie": "advertisement",
    "auto": "car",
    "beeldmerk": "logo",
    "bloem": "flower",
    "boom": "tree",
    "boot": "boat",
    "bril": "glasses",
    "brood": "bread",
    "brug": "bridge",
    "fabriek": "factory",
    "dier": "animal",
    "fiets": "bicycle",
    "figuur": "human figure",
    "gebouw": "building",
    "fles": "bottle",
    "foto": "photograph",
    "handschrift": "handwriting",
    "handtekening": "signature",
    "heilige": "saint",
    "hoed": "hat",
    "hond": "dog",
    "horloge": "watch",
    "huis": "house",
    "illustratie": "illustration",
    "initiaal": "decorated initial",
    "jurk": "dress",
    "kaart": "map",
    "kat": "cat",
    "kerk": "church",
    "kind": "child",
    "klok": "clock",
    "koe": "cow",
    "kroon": "crown",
    "lamp": "lamp",
    "logo": "logo",
    "man": "man",
    "melk": "milk carton",
    "molen": "windmill",
    "paard": "horse",
    "persoon": "person",
    "plant": "plant",
    "pijp": "pipe",
    "pistool": "pistol",
    "portret": "portrait",
    "puzzel": "crossword puzzle",
    "schaakprobleem": "chess diagram",
    "schip": "ship",
    "schoen": "shoe",
    "sigaar": "cigar",
    "sigaret": "cigarette",
    "sigarettenpakje": "cigarette pack",
    "slede": "sled",
    "slee": "sled",
    "spotprent": "cartoon",
    "stoel": "chair",
    "strip": "comic strip",
    "tabel": "table",
    "tafel": "table",
    "tekening": "drawing",
    "toilet": "toilet",
    "trein": "train",
    "vignet": "ornament",
    "vlag": "flag",
    "vliegtuig": "airplane",
    "vogel": "bird",
    "vrouw": "woman",
    "wapen": "coat of arms",
    "wapenschild": "heraldic shield",
    "wc": "toilet",
    "weerkaart": "weather map",
    "worst": "sausage",
}

# "Alles detecteren" (7.4); overlapping duplicates (IoU >= 0.8) are merged.
# Eight terms, eight SAM calls (about $0.02, functional design 6.4).
ALLES = ["illustration", "portrait", "coat of arms", "drawing", "photograph", "map", "decorated initial", "logo"]

# Snel zoeken (functional design 7.2): groups for what is on Commons. Key, the
# i18n key of the label (frontend/i18n), and the prompt set.
CATEGORIEEN = {
    "heraldiek": ("quick.heraldry", ["coat of arms", "heraldic shield"]),
    "portretten": ("quick.portraits", ["portrait"]),
    "figuren": ("quick.figures", ["person", "human figure"]),
    "dieren": ("quick.animals", ["animal", "bird"]),
    "planten": ("quick.plants", ["plant", "flower"]),
    "gebouwen": ("quick.buildings", ["building", "church"]),
    "kaarten": ("quick.maps", ["map"]),
    "schepen": ("quick.ships", ["ship", "boat"]),
    "initialen": ("quick.initials", ["decorated initial", "ornament"]),
    "logos": ("quick.logos", ["logo", "trademark"]),
    "tekst": ("quick.text", ["handwriting", "text block"]),
    "albumfotos": ("quick.album_photos", ["photograph"]),
}


# English labels to Dutch, for display. The reverse of VERTAALTABEL (first
# Dutch word wins), with preferred names and the category terms added.
NAMEN_NL = {}
for _nl, _en in VERTAALTABEL.items():
    NAMEN_NL.setdefault(_en, _nl)
NAMEN_NL.update(
    {
        "chess diagram": "schaakdiagram",
        "coat of arms": "wapen",
        "comic strip": "strip",
        "crossword puzzle": "kruiswoordpuzzel",
        "decorated initial": "initiaal",
        # Found with a click on the page (Aanwijzen): no search term, so no name.
        "klik": "aangewezen object",
        # Region from the structured data on Commons (P180 with P2677).
        "regio": "regio",
        "logo": "logo",
        "heraldic shield": "wapenschild",
        "human figure": "figuur",
        "text block": "tekstblok",
        "sled": "slee",
        "table": "tabel",
        "trademark": "handelsmerk",
        "weather map": "weerkaart",
    }
)


def dutch(label):
    """Dutch display name of an (English) label; unknown labels stay as they are."""
    if not label:
        return label
    return NAMEN_NL.get(label.strip().lower(), label)


def translate(term):
    """English noun phrase for a (possibly Dutch) term."""
    return VERTAALTABEL.get(term.strip().lower(), term.strip().lower())


def parse_prompt(text):
    """Split a prompt into terms to include and to exclude.

    Returns {"plus": [...], "min": [...]} with each entry
    {"term": original, "en": english}. Duplicates are removed.
    """
    result = {"plus": [], "min": []}
    text = (text or "").strip()
    if not text:
        return result
    pieces = _OPERATOR.split(text)
    # re.split with one capture group: [term, op, term, op, term, ...];
    # the group is None for the ",", "+" and "-" alternatives.
    separators = list(_OPERATOR.finditer(text))
    terms = pieces[::2]
    modes = ["plus"]
    for match in separators:
        word = (match.group(1) or match.group(0)).strip().lower()
        modes.append("min" if word in _EXCLUDE or word == "-" else "plus")
    seen = set()
    for term, mode in zip(terms, modes):
        term = (term or "").strip()
        if not term:
            continue
        english = translate(term)
        if (mode, english) in seen:
            continue
        seen.add((mode, english))
        result[mode].append({"term": term, "en": english})
    return result
