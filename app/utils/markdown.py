import markdown


_md = markdown.Markdown(
    extensions=["fenced_code", "tables", "toc", "attr_list", "nl2br"],
    output_format="html",
)


def render_markdown(text: str) -> str:
    """Render Markdown text to HTML."""
    _md.reset()
    return _md.convert(text)
