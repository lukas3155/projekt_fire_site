from app.utils.seo import generate_slug


def test_basic_slug():
    assert generate_slug("Hello World") == "hello-world"


def test_polish_characters():
    assert generate_slug("Jak zacząć inwestować") == "jak-zaczac-inwestowac"


def test_all_polish_chars():
    assert generate_slug("ąćęłńóśźż ĄĆĘŁŃÓŚŹŻ") == "acelnoszz-acelnoszz"


def test_special_characters():
    assert generate_slug("C++ and C# — together!") == "c-and-c-together"


def test_multiple_spaces():
    assert generate_slug("  lots   of   spaces  ") == "lots-of-spaces"


def test_numbers():
    assert generate_slug("Top 10 ETF w 2024") == "top-10-etf-w-2024"


def test_empty_string():
    assert generate_slug("") == ""
