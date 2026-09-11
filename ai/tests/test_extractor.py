import pytest
from app.nlp.extractor import RequirementExtractor
from app.schemas.requirements import ExtractedRequirements


def test_transformer_and_source_offsets():
    text = "11KV/433V three phase oil immersed distribution\ntransformer for outdoor installation with insulation and efficiency testing"
    r = RequirementExtractor().extract(text)
    assert r.product == "distribution transformer"
    assert r.phase == ["three_phase"] and r.product_type == ["oil immersed"]
    assert [(v.value, v.unit) for v in r.voltages] == [(11, "kV"), (433, "V")]
    assert r.installation == ["outdoor"]
    assert r.testing_requirements == ["insulation testing", "efficiency testing"]
    for items in r.evidence.values():
        for item in items:
            assert text[item.start:item.end] == item.evidence


@pytest.mark.parametrize("text,field,expected", [
    ("IP65 LED road lighting fixture suitable for outdoor installation", "ip_ratings", ["IP65"]),
    ("33 kV XLPE insulated high voltage power cable", "materials", ["XLPE"]),
    ("protective headgear against falling objects", "safety_requirements", ["against falling objects"]),
    ("made of aluminum with BIS certification required", "materials", ["aluminium"]),
    ("Class A, Class B, Class F and Class H", "technical_classes", ["Class A", "Class B", "Class F", "Class H"]),
    ("indoor outdoor underground overhead weatherproof waterproof", "environment", ["weatherproof", "waterproof"])])
def test_fields(text, field, expected):
    assert getattr(RequirementExtractor().extract(text), field) == expected


def test_pump_pipe_and_categories():
    pump = RequirementExtractor().extract("centrifugal water pump rated 15 kW at 50 Hz")
    assert pump.product == "pump" and pump.power_ratings[0].value == 15 and pump.frequencies[0].unit == "Hz"
    pipe = RequirementExtractor().extract("PVC pressure pipe of 110 mm diameter for potable water")
    assert pipe.product == "PVC water pipe" and pipe.materials == ["PVC"]
    assert pipe.dimensions[0].kind == "diameter" and pipe.dimensions[0].value == 110
    r = RequirementExtractor().extract("Made of copper. Must comply with electrical safety requirements. Minimum efficiency of 95%. BIS certification required.")
    assert r.material_requirements and r.safety_requirements and r.performance_requirements and r.certification_requirements


def test_negation_is_retained_as_evidence_not_positive_enrichment():
    text = "Not suitable for indoor use. No copper. Outdoor installation required. Insulation testing is not required."
    r = RequirementExtractor().extract(text)
    assert r.installation == ["outdoor"] and not r.materials and not r.testing_requirements
    assert any(e.negated for e in r.evidence["installation"])


def test_no_number_or_product_guessing_and_safe_defaults():
    r = RequirementExtractor().extract("ergonomic office chair order 123 for 50 users")
    assert r.product is None and r.technical_attribute_count == 0
    assert not RequirementExtractor().extract("100 kVA").voltages
    a, b = ExtractedRequirements(), ExtractedRequirements()
    a.materials.append("steel")
    assert not b.materials
