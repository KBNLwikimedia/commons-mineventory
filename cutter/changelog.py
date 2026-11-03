"""CHANGELOG.md as structured data for the changelog page with facets:
versions (number, date), each with its sections (Toegevoegd, Gewijzigd,
Opgelost, …) and per section the separate items, rendered to HTML."""

import re

from . import markdown_lite

_VERSION = re.compile(r"^## \[([^\]]+)\](?:\s*-\s*(\S+))?\s*$")
_SECTION = re.compile(r"^### (.+?)\s*$")


def _items(lines):
    """Top-level bullets (with their indented continuation) as separate
    Markdown blocks; loose text becomes an item of its own."""
    items, current = [], []
    for line in lines:
        if line.startswith("- ") or (not line.startswith(" ") and line.strip() and not current):
            if current:
                items.append("\n".join(current))
            current = [line]
        elif line.strip() or current:
            current.append(line)
    if current:
        items.append("\n".join(current))
    return [item.strip() for item in items if item.strip()]


def _plain(markdown):
    return " ".join(re.sub(r"[`*_\[\]()]|https?://\S+", " ", markdown).split())


def parse(text):
    """{"intro": html, "versies": [{"versie", "datum", "reeks", "secties":
    [{"soort", "items": [{"html", "tekst"}]}]}]} in document order."""
    intro, versions = [], []
    version = section = None
    lines = []

    def close_section():
        if version is not None and section is not None:
            items = [{"html": markdown_lite.render(item), "tekst": _plain(item)} for item in _items(lines)]
            if items:
                version["secties"].append({"soort": section, "items": items})
        lines.clear()

    for line in text.splitlines():
        match = _VERSION.match(line)
        if match:
            close_section()
            section = None
            number, date = match.group(1), match.group(2) or ""
            series = ".".join(number.split(".")[:2]) if re.match(r"^\d+\.\d+", number) else number
            version = {"versie": number, "datum": date, "reeks": series, "secties": []}
            versions.append(version)
            continue
        match = _SECTION.match(line)
        if match and version is not None:
            close_section()
            section = match.group(1)
            continue
        if version is None:
            intro.append(line)
        elif section is not None:
            lines.append(line)
    close_section()
    intro_text = "\n".join(line for line in intro if not line.startswith("# "))
    return {"intro": markdown_lite.render(intro_text), "versies": [v for v in versions if v["secties"]]}
