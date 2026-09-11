import pytest
from app.nlp.preprocess import clean_text


def test_preserves_technical_meaning():
    assert clean_text("  Not\r\nsuitable for indoor use: 11 kV / 433 V,\t50 Hz; 10 × 20 mm ±5%. ") == "Not suitable for indoor use: 11 kV / 433 V, 50 Hz; 10 × 20 mm ±5%."


@pytest.mark.parametrize("text", ["", " \n\t", "\ufeff\u200b\x00"])
def test_empty_noise(text):
    assert clean_text(text) == ""


def test_extraction_noise():
    assert clean_text("trans\u00adformer\x00 rated\u00a0power") == "transformer rated power"
