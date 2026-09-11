"""Script hints for demo routing, not general language identification."""
import unicodedata


def detect_language(text):
    devanagari = sum(0x0900 <= ord(c) <= 0x097F and unicodedata.category(c).startswith("L") for c in text)
    kannada = sum(0x0C80 <= ord(c) <= 0x0CFF and unicodedata.category(c).startswith("L") for c in text)
    if kannada > devanagari:
        return "kannada"
    if devanagari:
        return "hindi"
    return "english"
