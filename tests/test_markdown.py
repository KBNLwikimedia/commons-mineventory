from cutter.markdown_lite import render


def test_headings_lists_and_inline():
    html = render(
        "# Titel\n\nTekst met `code`, **vet** en [link](https://example.org).\n\n"
        "## [1.0] - 2026\n\n### Toegevoegd\n\n- een\n- twee met *nadruk*\n  vervolg\n\n### Toegevoegd\n"
    )
    assert '<h1 id="titel">Titel</h1>' in html
    assert "<code>code</code>" in html and "<strong>vet</strong>" in html
    assert '<a href="https://example.org">link</a>' in html
    assert html.count("<li>") == 2 and "<em>nadruk</em>" in html and "vervolg" in html
    assert 'id="toegevoegd"' in html and 'id="toegevoegd-2"' in html


def test_escapes_html_and_unsafe_links():
    html = render("<script>alert(1)</script> [x](javascript:alert(1)) `<b>`")
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "javascript:" not in html.split("href=")[-1] if "href=" in html else True
    assert "<code>&lt;b&gt;</code>" in html


def test_changelog_page(http):
    page = http.get("/changelog").get_data(as_text=True)
    assert 'class="cl-versie"' in page
    assert 'id="cc-changelog-filter"' in page
    assert 'id="cc-changelog-tabel"' in page
    assert 'class="cl-item" data-versie=' in page
    assert http.get("/changelog.md").mimetype == "text/plain"


def test_changelog_parse():
    from cutter.changelog import parse

    text = """# Changelog

Intro.

## [Unreleased]

## [0.2.1] - 2026-11-02

### Toegevoegd

- **Een** ding.
  - met een onderdeel
- Nog iets.

### Opgelost

- Een fout.

## [0.2.0] - 2026-11-01

### Gewijzigd

- Anders.
"""
    data = parse(text)
    assert [v["versie"] for v in data["versies"]] == ["0.2.1", "0.2.0"]  # Unreleased without items drops out
    first = data["versies"][0]
    assert first["datum"] == "2026-11-02" and first["reeks"] == "0.2"
    assert [(s["soort"], len(s["items"])) for s in first["secties"]] == [("Toegevoegd", 2), ("Opgelost", 1)]
    assert "<strong>Een</strong>" in first["secties"][0]["items"][0]["html"] and "onderdeel" in first["secties"][0]["items"][0]["tekst"]
    assert "Intro." in data["intro"]
