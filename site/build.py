"""Build the GitHub Pages site: the landing page plus the documentation as HTML.

Usage: python site/build.py [output_dir]   (default: _site)

The site is documentation and explanation only; the working app runs on Toolforge.
Markdown is rendered here with python-markdown instead of Jekyll, because Jekyll's
Liquid would swallow the many {{Template}} examples in the docs.
"""

import html
import posixpath
import re
import shutil
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SITE_SRC = ROOT / "site"
REPO_URL = "https://github.com/KBNLwikimedia/commons-mineventory"
BLOB_URL = REPO_URL + "/blob/main/"

# Repo path -> (output path, title in the menu). Order is the menu order.
DOCS = {
    "docs/functioneel-ontwerp.md": ("docs/functioneel-ontwerp.html", "Functioneel ontwerp"),
    "docs/api.md": ("docs/api.html", "REST-API"),
    "docs/artwork-velden.md": ("docs/artwork-velden.html", "Velden per sjabloon"),
    "docs/privacy.md": ("docs/privacy.html", "Privacy"),
    "docs/privacy.en.md": ("docs/privacy.en.html", "Privacy (English)"),
    "docs/overdracht.md": ("docs/overdracht.html", "Overdracht"),
    "docs/ontwerp-wat-is-dit.md": ("docs/ontwerp-wat-is-dit.html", "Ontwerp: Wat staat hierop?"),
    "BACKLOG.md": ("backlog.html", "Backlog"),
    "CHANGELOG.md": ("changelog.html", "Changelog"),
}

LINK_RE = re.compile(r'(<a\s[^>]*?href=")([^"]+)(")')

TEMPLATE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} – Commons Mineventory</title>
<link rel="icon" href="{base}icoon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{base}docs.css">
</head>
<body>
<header class="top"><div class="wrap">
  <a class="brand" href="{base}index.html"><img src="{base}icoon.svg" alt="">Commons Mineventory</a>
  <span class="tag">experiment</span>
  <nav class="links"><a href="{base}index.html">Home</a><a href="{base}docs/index.html">Documentatie</a><a href="{repo}">GitHub</a></nav>
</div></header>
<div class="wrap layout">
  <nav class="menu" aria-label="Documentatie">
    <p class="menu-title">Documentatie</p>
    <ul>{menu}</ul>
    {toc}
  </nav>
  <main class="doc">
    <p class="source">Bron: <a href="{source_url}">{source}</a> op GitHub</p>
    {body}
  </main>
</div>
<footer><div class="wrap">
  <p>Dit is een experiment. Het is geen officiële dienst van de KB, nationale bibliotheek, of van de Wikimedia Foundation. Aan deze toepassing kunnen geen rechten worden ontleend.</p>
  <p>Code onder de MIT-licentie. Deze pagina laadt niets van derden.</p>
</div></footer>
</body>
</html>
"""


def rewrite_links(body, source):
    """Point .md links to the rendered pages; other repo files to GitHub."""
    out_path = DOCS[source][0]

    def fix(match):
        href = html.unescape(match.group(2))
        if re.match(r"^[a-z]+:|^#|^//", href):
            return match.group(0)
        path, _, anchor = href.partition("#")
        target = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
        if target in DOCS:
            new = posixpath.relpath(DOCS[target][0], posixpath.dirname(out_path) or ".")
        else:
            new = BLOB_URL + target
        if anchor:
            new += "#" + anchor
        return match.group(1) + html.escape(new) + match.group(3)

    return LINK_RE.sub(fix, body)


def render(source, out_dir):
    out_path, title = DOCS[source]
    text = (ROOT / source).read_text(encoding="utf-8")
    md = markdown.Markdown(
        extensions=["extra", "sane_lists", "toc"],
        extension_configs={"toc": {"permalink": "¶", "toc_depth": "2-3"}},
    )
    body = rewrite_links(md.convert(text), source)
    base = "../" * out_path.count("/")
    menu = "".join(
        '<li><a href="{href}"{cur}>{name}</a></li>'.format(
            href=base + dst, name=html.escape(name), cur=' aria-current="page"' if src == source else ""
        )
        for src, (dst, name) in DOCS.items()
    )
    toc = ""
    if md.toc_tokens and sum(1 for _ in md.toc_tokens) > 2:
        toc = '<p class="menu-title">Op deze pagina</p>' + md.toc
    page = TEMPLATE.format(
        lang="en" if source.endswith(".en.md") else "nl",
        title=html.escape(title),
        base=base,
        repo=REPO_URL,
        menu=menu,
        toc=toc,
        source=html.escape(source),
        source_url=BLOB_URL + source,
        body=body,
    )
    target = out_dir / out_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")


def docs_index(out_dir):
    items = "".join(
        '<li><a href="../{href}">{name}</a> <span class="file">{src}</span></li>'.format(
            href=dst, name=html.escape(name), src=html.escape(src)
        )
        for src, (dst, name) in DOCS.items()
    )
    body = (
        "<h1>Documentatie</h1>"
        "<p>De documentatie van de Commons Mineventory, in het Nederlands. Begin bij het "
        '<a href="functioneel-ontwerp.html">functioneel ontwerp</a>; wie het werk overneemt, leest ook de '
        '<a href="overdracht.html">overdracht</a>. De werkende app komt op Wikimedia Toolforge.</p>'
        '<ul class="doclist">' + items + "</ul>"
    )
    page = TEMPLATE.format(
        lang="nl", title="Documentatie", base="../", repo=REPO_URL,
        menu="".join('<li><a href="../{0}">{1}</a></li>'.format(d, html.escape(n)) for d, n in DOCS.values()),
        toc="", source="docs/", source_url=REPO_URL + "/tree/main/docs", body=body,
    )
    (out_dir / "docs").mkdir(parents=True, exist_ok=True)
    (out_dir / "docs" / "index.html").write_text(page, encoding="utf-8")


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Empty the folder rather than removing it, so a preview server serving it can keep running.
    for child in out_dir.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    for name in ("index.html", "docs.css"):
        shutil.copy2(SITE_SRC / name, out_dir / name)
    shutil.copy2(ROOT / "static" / "img" / "icoon.svg", out_dir / "icoon.svg")
    shutil.copytree(ROOT / "docs" / "screenshots", out_dir / "screenshots")
    for source in DOCS:
        render(source, out_dir)
    docs_index(out_dir)
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    print("Site gebouwd in", out_dir)


if __name__ == "__main__":
    main()
