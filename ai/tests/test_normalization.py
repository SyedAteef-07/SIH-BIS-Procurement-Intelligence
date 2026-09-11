import pytest
from app.nlp.normalization import normalize_phase, normalize_technical_value, normalize_ip_rating


@pytest.mark.parametrize("text", ["3 phase", "3-phase", "three phase", "three-phase"])
def test_three_phase(text):
    assert normalize_phase(text) == "three_phase"


@pytest.mark.parametrize("text", ["1 phase", "single phase", "single-phase"])
def test_single_phase(text):
    assert normalize_phase(text) == "single_phase"


@pytest.mark.parametrize("text,value,unit", [("11KV", 11, "kV"), ("11 kV", 11, "kV"), ("11kv", 11, "kV"),
    ("433 V", 433, "V"), ("33KV", 33, "kV"), ("230 volts", 230, "V"), ("50 Hz", 50, "Hz"), ("60Hz", 60, "Hz"),
    ("100 kVA", 100, "kVA"), ("5 MVA", 5, "MVA"), ("10 kW", 10, "kW"), ("2 MW", 2, "MW"),
    ("110 mm", 110, "mm"), ("5 cm", 5, "cm"), ("1.5 m", 1.5, "m")])
def test_quantities(text, value, unit):
    result = normalize_technical_value(text)
    assert (result.raw, result.value, result.unit) == (text, value, unit)


@pytest.mark.parametrize("text", ["IP65", "ip65", "IP 65"])
def test_ip(text):
    assert normalize_ip_rating(text) == "IP65"


@pytest.mark.parametrize("text", ["123", "order11KV", "11kVery", "-5 kV"])
def test_reject_non_measurements(text):
    with pytest.raises(ValueError):
        normalize_technical_value(text)


def test_rejects_overflow():
    with pytest.raises(ValueError, match="finite"):
        normalize_technical_value("9" * 400 + " kV")
