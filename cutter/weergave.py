"""Clean the HTML that Commons renders from the wikitext (action=parse), so the
Commons concept can show it as a preview.

Only an allowlist of tags and attributes is kept. Images, <style> and
<script> are dropped (the Wikidata logo and the "Edit this at Wikidata" pencil
become small icons drawn by our own CSS), as are inline styles that load something (url(...)):
the browser of the user then never contacts Wikimedia for this preview
(privacy on Toolforge). Links point to Commons and open in a new tab.
"""

import re
from html import escape
from html.parser import HTMLParser
from urllib.parse import urljoin

COMMONS = "https://commons.wikimedia.org"

TAGS = {
    "a", "abbr", "b", "bdi", "big", "blockquote", "br", "caption", "center", "code", "dd", "del", "div", "dl", "dt",
    "em", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i", "ins", "kbd", "li", "ol", "p", "pre", "q", "s", "small",
    "span", "strong", "sub", "sup", "table", "tbody", "td", "tfoot", "th", "thead", "time", "tr", "u", "ul",
}
VOID = {"br", "hr"}
DROP_WITH_CONTENT = {"script", "style", "noscript", "template", "iframe", "object"}
ATTRIBUTES = {"class", "style", "title", "lang", "dir", "colspan", "rowspan", "href", "datetime"}


def _safe_style(value):
    low = value.lower()
    return not any(bad in low for bad in ("url(", "expression", "javascript:", "@import", "behavior"))


def _safe_href(value):
    href = urljoin(COMMONS + "/wiki/", value.strip())
    return href if href.startswith(("https://", "http://")) else None


def _icon(link_title):
    """An icon of our own for an image that links to Wikidata, else None."""
    if link_title.startswith("wikidata:"):
        return '<span class="cc-ikoon cc-ikoon-wikidata" title="Wikidata"></span>'
    if link_title == "Edit this at Wikidata":
        return '<span class="cc-ikoon cc-ikoon-bewerken" title="Edit this at Wikidata"></span>'
    return None


class _Cleaner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0  # depth inside a dropped element with content
        self.open = []
        self.links = []  # title of each open <a>, to recognise Wikidata icons

    def handle_starttag(self, tag, attrs):
        if self.skip or tag in DROP_WITH_CONTENT:
            if tag in DROP_WITH_CONTENT:
                self.skip += 1
            return
        if tag == "img":
            icon = _icon(self.links[-1] if self.links else "")
            if icon:
                self.out.append(icon)
            return
        if tag not in TAGS:
            return
        kept = []
        for name, value in attrs:
            # The row ids of the information templates (fileinfotpl_desc, …): the
            # interface puts its pencils there. No other ids.
            if name == "id" and value and re.fullmatch(r"fileinfotpl_[a-z_]{1,40}", value):
                kept.append(f' id="{value}"')
                continue
            if name not in ATTRIBUTES or value is None:
                continue
            if name == "style" and not _safe_style(value):
                continue
            if name == "href":
                value = _safe_href(value)
                if not value:
                    continue
            kept.append(f' {name}="{escape(value, quote=True)}"')
        if tag == "a":
            kept.append(' target="_blank" rel="noopener"')
            self.links.append(dict(attrs).get("title") or "")
        self.out.append(f"<{tag}{''.join(kept)}>")
        if tag not in VOID:
            self.open.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in self.open and self.open[-1] == tag and tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in DROP_WITH_CONTENT:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip or tag not in TAGS or tag in VOID or tag not in self.open:
            return
        # Close what is still open up to this tag (MediaWiki output is well formed).
        while self.open:
            last = self.open.pop()
            if last == "a" and self.links:
                self.links.pop()
            self.out.append(f"</{last}>")
            if last == tag:
                break

    def handle_data(self, data):
        if not self.skip:
            self.out.append(escape(data, quote=False))


def clean_html(html):
    """The rendered page, limited to safe tags and attributes."""
    cleaner = _Cleaner()
    cleaner.feed(html or "")
    cleaner.close()
    cleaner.out.extend(f"</{tag}>" for tag in reversed(cleaner.open))
    return "".join(cleaner.out)
