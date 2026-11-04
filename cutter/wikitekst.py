"""Reading the wikitext of a Commons file page (functional design 5.2, 5.3, 7.5).

A small template parser, enough for what the app needs from a file page: the
licence templates, {{Information}} / {{Artwork}} / {{Photograph}} / {{Book}},
the rights templates ({{Personality rights}}, {{Trademarked}}, {{Delete}} …),
file notes ({{ImageNote}}) and {{Image extracted}}. Writing new wikitext for a
cut-out is in concept.py.
"""

import html
import math
import re
from dataclasses import dataclass, field

# Section headings under which Commons pages keep their licence templates.
LICENSE_HEADINGS = ("{{int:license-header}}", "license", "licensing", "licentie", "lizenz", "licence")

# Information-like templates whose fields the cut-out can take over (9.3).
INFO_TEMPLATES = ("information", "artwork", "photograph", "book", "art photo", "map")

# Templates that never come along to a cut-out (9.3): reviews, assessments,
# maintenance and deletion templates, and the extraction bookkeeping.
NEVER_COPIED = {
    "flickrreview", "licensereview", "license review", "ipernityreview", "picasareview",
    "assessments", "qi", "quality image", "fp", "featured picture", "vi", "valued image",
    "delete", "copyvio", "speedydelete", "speedy", "no permission since", "no license since",
    "no source since", "image extracted", "extracted from", "check categories", "uncategorized",
    "imagenote", "imagenoteend", "personality rights", "trademarked",
}

LICENSE_NAME = re.compile(
    r"^(self|cc-|cc0|cc-zero|pd-|pd |gfdl|gpl|lgpl|fal|attribution|copyrighted free use|"
    r"bild-|licen[cs]e|flickrreview|licensereview|ogl|etalab|kopimi|no restrictions|"
    r"public domain|anonymous-eu|cc by|nara|usgov|youtube|wikimedia)",
    re.IGNORECASE,
)


@dataclass
class Template:
    """One template call: its name (normalised: lower case, single spaces,
    no underscores), its parameters (positional ones as "1", "2", …), the raw
    wikitext and its position. `keys` maps each lower-case parameter name to
    its original spelling ({{Book}} uses |Date=, {{Artwork}} |date=)."""

    name: str
    params: dict = field(default_factory=dict)
    raw: str = ""
    start: int = 0
    end: int = 0
    keys: dict = field(default_factory=dict)

    def positional(self):
        return [v for k, v in sorted(self.params.items(), key=lambda kv: int(kv[0])) if k.isdigit()]


def normalise_name(name):
    name = re.sub(r"<!--.*?-->", "", name, flags=re.S)
    name = " ".join(name.replace("_", " ").split()).lower()
    return name.removeprefix("template:").removeprefix("sjabloon:").strip()


def _split_top_level(text, separator="|"):
    """Split on `separator` outside nested {{ }}, [[ ]] and {{{ }}}."""
    parts, depth, current, i = [], 0, [], 0
    while i < len(text):
        two = text[i : i + 2]
        if two in ("{{", "[["):
            depth += 1
            current.append(two)
            i += 2
            continue
        if two in ("}}", "]]") and depth:
            depth -= 1
            current.append(two)
            i += 2
            continue
        if text[i] == separator and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(text[i])
        i += 1
    parts.append("".join(current))
    return parts


def templates(text, nested=False):
    """Template calls in `text`, in document order. Top-level only, unless
    `nested` (then also the templates inside parameters)."""
    text = text or ""
    found, stack, i = [], [], 0
    while i < len(text) - 1:
        two = text[i : i + 2]
        if two == "{{" and text[i : i + 3] != "{{{":
            stack.append(i)
            i += 2
        elif two == "}}" and stack:
            start = stack.pop()
            if nested or not stack:
                call = _template(text, start, i + 2)
                if not call.name.startswith(("#", "int:", "subst:")):  # parser functions and magic words
                    found.append(call)
            i += 2
        else:
            i += 1
    return sorted(found, key=lambda t: t.start)


def _template(text, start, end):
    inner = text[start + 2 : end - 2]
    parts = _split_top_level(inner)
    params, keys, position = {}, {}, 0
    for part in parts[1:]:
        key, sep, value = part.partition("=")
        if sep and re.fullmatch(r"\s*[^{}\[\]|=]+?\s*", key):
            params[key.strip().lower()] = value.strip()
            keys[key.strip().lower()] = key.strip()
        else:
            position += 1
            params[str(position)] = part.strip()
    return Template(normalise_name(parts[0]), params, text[start:end], start, end, keys)


def names(text):
    """The names of all templates in the text, nested ones included."""
    return {t.name for t in templates(text, nested=True)}


def license_section(text):
    """The wikitext under the licence heading (up to the next heading of the
    same or a higher level), or None."""
    pattern = re.compile(r"^(=+)\s*(.*?)\s*\1\s*$", re.M)
    headings = list(pattern.finditer(text or ""))
    for index, heading in enumerate(headings):
        title = heading.group(2).strip().lower()
        if any(h in title for h in LICENSE_HEADINGS):
            level = len(heading.group(1))
            end = len(text)
            for later in headings[index + 1 :]:
                if len(later.group(1)) <= level:
                    end = later.start()
                    break
            return text[heading.end() : end]
    return None


def license_templates(text):
    """The licence templates of the original, verbatim (9.3): all templates in
    the licence section, or, without that section, the templates that look
    like licences. Review and deletion templates are left out."""
    section = license_section(text)
    candidates = templates(section) if section is not None else [t for t in templates(text) if LICENSE_NAME.match(t.name)]
    return [t.raw for t in candidates if t.name not in NEVER_COPIED and t.name not in INFO_TEMPLATES]


def info_template(text):
    """The first {{Information}}-like template (name and parameters), or None."""
    return next((t for t in templates(text) if t.name in INFO_TEMPLATES), None)


def image_notes(text):
    """File notes of the ImageAnnotator gadget: {{ImageNote|id=|x=|y=|w=|h=|
    dimx=|dimy=}} text {{ImageNoteEnd|id=}}. Coordinates are relative to
    dimx × dimy (the image size when the note was made)."""
    notes = []
    calls = templates(text)
    for index, call in enumerate(calls):
        if call.name != "imagenote":
            continue
        end = next((c for c in calls[index + 1 :] if c.name == "imagenoteend"), None)
        body = text[call.end : end.start] if end else ""
        try:
            values = {k: float(call.params[k]) for k in ("x", "y", "w", "h", "dimx", "dimy")}
        except (KeyError, ValueError):
            continue
        if not all(math.isfinite(v) for v in values.values()) or values["dimx"] <= 0 or values["dimy"] <= 0:
            continue
        notes.append({"id": call.params.get("id", str(len(notes) + 1)), "tekst": plain_text(body), **values})
    return notes


def extracted_files(text):
    """Files named in {{Image extracted}} on the original (existing cut-outs)."""
    result = []
    for call in templates(text, nested=True):
        if call.name not in ("image extracted", "extracted images"):
            continue
        for value in call.params.values():
            value = value.strip()
            if value and "." in value:
                title = value if value.lower().startswith("file:") else f"File:{value}"
                result.append(title.replace("_", " "))
    return list(dict.fromkeys(result))


def plain_text(wikitext, limit=None):
    """Readable text from wikitext or HTML: language templates and links keep
    their text, other templates, tags and comments go."""
    text = wikitext or ""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    # {{en|1=text}} / {{nl|text}} keep their text.
    text = re.sub(r"\{\{\s*[a-z]{2,3}(?:-[a-z]+)?\s*\|\s*(?:1\s*=\s*)?([^{}]*)\}\}", r" \1 ", text, flags=re.I)
    for _ in range(5):  # nested templates, inside out
        text, count = re.subn(r"\{\{[^{}]*\}\}", " ", text)
        if not count:
            break
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", text)
    # Hidden machine data in Commons' HTML (e.g. "date QS:P,+1450…" in a display:none span).
    text = re.sub(r"<(span|div)[^>]*display:\s*none[^>]*>.*?</\1>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"'{2,}", "", text)
    text = " ".join(html.unescape(text).split())
    if limit and len(text) > limit:
        text = text[:limit].rstrip() + "…"
    return text


__all__ = [
    "Template", "templates", "names", "license_section", "license_templates", "info_template",
    "image_notes", "extracted_files", "plain_text", "normalise_name", "NEVER_COPIED",
]
