import re

import markdown


_md = markdown.Markdown(
    extensions=["fenced_code", "tables", "toc", "attr_list"],
    output_format="html",
)

_IMG_TAG_RE = re.compile(r"<img\b(?![^>]*\bloading=)")


def render_markdown(text: str) -> str:
    """Render Markdown text to HTML."""
    _md.reset()
    html = _md.convert(text)
    html = _IMG_TAG_RE.sub('<img loading="lazy"', html)
    return html
