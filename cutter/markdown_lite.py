"""A small Markdown-to-HTML converter for the app's own documents (CHANGELOG).

Supports what those documents use: headings, bullet lists (also nested by
indentation), paragraphs, `code`, **bold**, *italic* and [links](url).
Everything is HTML-escaped first, so the output is safe to insert.
"""

import html
import re

_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<![\w*])\*([^*\s][^*]*)\*(?![\w*])")


def _inline(text):
    text = html.escape(text, quote=False)
    codes = []

    def keep_code(match):
        codes.append(f"<code>{match.group(1)}</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = _CODE.sub(keep_code, text)  # no other markup inside code
    text = _LINK.sub(
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>'
        if re.match(r"^(https?://|/|#)", m.group(2))
        else m.group(0),
        text,
    )
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def render(markdown):
    """HTML for a Markdown document."""
    out = []
    paragraph = []
    list_depths = []  # indentation of each open <ul>
    used_ids = {}

    def unique_id(text):
        slug = _slug(text) or "kop"
        used_ids[slug] = used_ids.get(slug, 0) + 1
        return slug if used_ids[slug] == 1 else f"{slug}-{used_ids[slug]}"

    def close_paragraph():
        if paragraph:
            out.append(f"<p>{_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_lists(to_depth=-1):
        while list_depths and list_depths[-1] > to_depth:
            list_depths.pop()
            out.append("</li></ul>")

    for line in markdown.splitlines():
        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        item = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if heading:
            close_paragraph()
            close_lists()
            level = len(heading.group(1))
            text = heading.group(2).strip()
            out.append(f'<h{level} id="{unique_id(text)}">{_inline(text)}</h{level}>')
        elif item:
            close_paragraph()
            depth = len(item.group(1).expandtabs(4))
            if not list_depths or depth > list_depths[-1]:
                out.append("<ul><li>")
                list_depths.append(depth)
            else:
                close_lists(depth)
                out.append("</li><li>")
            out.append(_inline(item.group(2)))
        elif not line.strip():
            close_paragraph()
        elif list_depths and line.startswith(" "):
            out.append(" " + _inline(line.strip()))  # continuation of a list item
        else:
            close_lists()
            paragraph.append(line.strip())
    close_paragraph()
    close_lists()
    return "\n".join(out)
