from app.utils.markdown import render_markdown


def test_basic_paragraph():
    result = render_markdown("Hello world")
    assert "<p>" in result
    assert "Hello world" in result


def test_heading():
    result = render_markdown("# Title")
    assert "<h1" in result
    assert "Title" in result


def test_bold():
    result = render_markdown("**bold text**")
    assert "<strong>bold text</strong>" in result


def test_link():
    result = render_markdown("[link](https://example.com)")
    assert 'href="https://example.com"' in result


def test_fenced_code():
    result = render_markdown("```python\nprint('hello')\n```")
    assert "<code" in result
    assert "print" in result


def test_image_lazy_loading():
    result = render_markdown("![alt](https://example.com/img.jpg)")
    assert 'loading="lazy"' in result
    assert "<img" in result


def test_table():
    md = "| A | B |\n|---|---|\n| 1 | 2 |"
    result = render_markdown(md)
    assert "<table>" in result
    assert "<td>" in result
