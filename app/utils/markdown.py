import re

import markdown


_md = markdown.Markdown(
    extensions=["fenced_code", "tables", "toc", "attr_list", "nl2br"],
    output_format="html",
)

_IMG_TAG_RE = re.compile(r"<img\b(?![^>]*\bloading=)")

# Matches lines that start a block element: list items or headings.
_BLOCK_START_RE = re.compile(r"^(\s*(?:[*\-+]|\d+\.)\s|#{1,6}\s)", re.MULTILINE)


def _preprocess_markdown(text: str) -> str:
    """Insert blank lines around block elements so nl2br doesn't break them.

    The nl2br extension converts every single newline to <br>, which prevents
    the Markdown parser from recognising list items and headings that aren't
    preceded by a blank line.  This preprocessor ensures blank lines exist
    before and after block-level runs (lists, headings).
    """
    lines = text.split("\n")
    result: list[str] = []
    for i, line in enumerate(lines):
        is_block = bool(_BLOCK_START_RE.match(line))
        prev = lines[i - 1] if i > 0 else ""
        prev_is_block = bool(_BLOCK_START_RE.match(prev)) if i > 0 else False

        # Insert blank line before a block line if prev is non-empty normal text
        if i > 0 and is_block and prev.strip() and not prev_is_block:
            result.append("")
        # Insert blank line before normal text if prev is a block line
        if i > 0 and not is_block and line.strip() and prev_is_block:
            result.append("")

        result.append(line)
    return "\n".join(result)


def render_markdown(text: str) -> str:
    """Render Markdown text to HTML."""
    _md.reset()
    html = _md.convert(_preprocess_markdown(text))
    html = _IMG_TAG_RE.sub('<img loading="lazy"', html)
    return html
