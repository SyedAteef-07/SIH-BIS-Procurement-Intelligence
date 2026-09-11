import pytest
from app.nlp.product_matcher import ProductMatcher


@pytest.mark.parametrize("text,expected", [("step-down transformers", "distribution transformer"),
    ("IP65 LED road lighting fixture", "street luminaire"), ("electrical cables", "power cable"),
    ("PVC pressure pipe", "PVC water pipe"), ("protective headgear", "safety helmet"),
    ("centrifugal water pump", "pump"), ("ergonomic office chair", None), ("transformer", None),
    ("not a distribution transformer", None), ("pump and power cable", None)])
def test_alias_evidence(text, expected):
    match = ProductMatcher().match(text)
    assert (match.value if match else None) == expected
    if match:
        assert text[match.start:match.end] == match.evidence


def test_custom_aliases_and_boundaries():
    matcher = ProductMatcher({"widget": ["special widget"]})
    assert matcher.match("special widgets").value == "widget"
    assert matcher.match("unspecial widget") is None
    assert matcher.match("pump") is None


def test_specific_product_wins_over_overlapping_generic():
    assert ProductMatcher().match("pump mechanical seals").value == "pump mechanical seal"
