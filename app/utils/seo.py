import re
import unicodedata


def generate_slug(text: str) -> str:
    """Generate a URL-friendly slug from text, handling Polish characters."""
    # Normalize unicode and transliterate Polish chars
    polish_map = {
        "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n",
        "ó": "o", "ś": "s", "ź": "z", "ż": "z",
        "Ą": "A", "Ć": "C", "Ę": "E", "Ł": "L", "Ń": "N",
        "Ó": "O", "Ś": "S", "Ź": "Z", "Ż": "Z",
    }
    for pl_char, ascii_char in polish_map.items():
        text = text.replace(pl_char, ascii_char)

    # Normalize remaining unicode to ASCII
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Lowercase
    text = text.lower()

    # Replace non-alphanumeric with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # Remove leading/trailing hyphens and collapse multiples
    text = re.sub(r"-+", "-", text).strip("-")

    return text
