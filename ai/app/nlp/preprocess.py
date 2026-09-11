import re
import unicodedata


def clean_text(text: str) -> str:
    """Normalize extraction noise without losing units, punctuation or negations."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u00ad", "").replace("\u200b", "").replace("\ufeff", "")
    text = "".join(c for c in text if not unicodedata.category(c).startswith("C") or c.isspace())
    return re.sub(r"\s+", " ", text).strip()
