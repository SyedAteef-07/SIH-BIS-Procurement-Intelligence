import pytest
from app.nlp.extractor import RequirementExtractor


@pytest.mark.parametrize('text,product,fields', [
    ('Portland cement compressive strength setting time soundness for concrete', 'Portland cement', ['compressive_strength','setting_time','soundness','construction_use']),
    ('safety helmet impact protection penetration resistance retention for industrial use', 'safety helmet', ['impact_protection','penetration_resistance','retention','construction_use']),
    ('water pump flow rate head hydraulic efficiency', 'pump', ['flow','head','hydraulic_efficiency','water_application']),
    ('low voltage PVC cable 1.1 kV 50 Hz for building wiring', 'power cable', ['pvc_insulation','voltages','frequencies','cable_application']),
    ('high voltage XLPE cable 33 kV underground dielectric testing', 'power cable', ['xlpe_insulation','voltages','underground_installation','dielectric_testing']),
])
def test_demo_topics(text, product, fields):
    extracted = RequirementExtractor().extract(text)
    assert extracted.product == product
    for field in fields:
        assert getattr(extracted, field)
        assert extracted.evidence[field]
        assert all(e.evidence in text and not e.negated for e in extracted.evidence[field])


def test_topic_specific_evidence_and_negation():
    result = RequirementExtractor().extract('Portland cement without soundness testing; setting time specified.')
    assert result.evidence['soundness'][0].negated
    assert result.soundness == []
    assert result.setting_time == ['setting time']
    assert not result.evidence['setting_time'][0].negated
    assert 'compressive_strength' not in result.evidence
