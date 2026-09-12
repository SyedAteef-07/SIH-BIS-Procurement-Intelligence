import pytest
from sqlalchemy import func, select
from app.database.models import StandardCertification, StandardRelationship
from app.scripts.seed_standards import seed_standards, DEMO_NOTE
from app.services.gap_analysis import analyze_gaps, ExtractedInput
from app.database.repositories.standards import StandardRepository
from conftest import ai_payload


def test_coverage_counts_and_score_independence(api):
    client, ai = api
    text = 'distribution transformer 11 kV three phase 50 Hz outdoor'
    fields = dict(voltages='11 kV', phase='three phase', frequencies='50 Hz', installation='outdoor')
    extraction = dict(product='distribution transformer', evidence={k: [dict(evidence=v)] for k, v in fields.items()})
    ai.payload = ai_payload(('IS-DEMO-001',), extracted_requirements=extraction)
    def analyze():
        response = client.post('/api/analyze', json={'description': text})
        assert response.status_code == 200
        return response.json()
    result = analyze()
    coverage = result['gap_analysis']
    assert coverage['coverage_percentage'] == 80.0
    assert (coverage['mentioned_count'], coverage['total_checks'], coverage['missing_count'], coverage['needs_review_count']) == (4, 5, 1, 0)
    ai.payload['recommendations'][0].update(retrieval_score=-999, reranker_score=12345)
    assert analyze()['gap_analysis'] == coverage
    ai.payload['extracted_requirements']['evidence'] = {}
    assert analyze()['gap_analysis']['coverage_percentage'] == 0.0
    ai.payload['extracted_requirements']['product'] = None
    assert analyze()['gap_analysis']['coverage_percentage'] == 0.0


def test_relationships_certifications_and_idempotence(database, api):
    _, sessions = database
    with sessions.begin() as session:
        seed_standards(session)
        seed_standards(session)
        assert session.scalar(select(func.count()).select_from(StandardRelationship)) == 15
        assert session.scalar(select(func.count()).select_from(StandardCertification)) == 5
        assert len(StandardRepository(session).get_related_standards(['IS-DEMO-001'])) == 4
    client, ai = api
    ai.payload = ai_payload(('IS-DEMO-001', 'IS-DEMO-010'))
    result = client.post('/api/analyze', json={'description': 'distribution transformer'}).json()
    assert [r['number'] for r in result['recommendations']] == ['IS-DEMO-001', 'IS-DEMO-010']
    related = result['related_standards']
    assert [r['standard_code'] for r in related[:4]] == ['IS-DEMO-014', 'IS-DEMO-015', 'IS-DEMO-016', 'IS-DEMO-025']
    assert [r['relationship_type'] for r in related[:4]] == ['material', 'test_method', 'component', 'safety']
    assert all(r['is_demo_relationship'] and not r['relationship_verified'] for r in related)
    assert all('not a verified BIS normative reference' in r['relationship_note'] for r in related)
    assert all(c['status'] == 'unverified' and c['applicable'] is None and c['note'] == DEMO_NOTE for c in result['certifications'])
    detail = client.get('/api/standards/IS-DEMO-001').json()
    assert len(detail['related']) == 4 and detail['certifications']
    # Even malformed demo metadata cannot be presented as officially verified.
    with sessions.begin() as session:
        cert = session.scalars(select(StandardCertification)).first()
        cert.status, cert.applicable = 'verified', True
    result = client.post('/api/analyze', json={'description': 'distribution transformer'}).json()
    assert all(c['status'] == 'unverified' and c['applicable'] is None for c in result['certifications'])


@pytest.mark.parametrize('product,code', [('Portland cement','002'), ('safety helmet','004'), ('pump','008'), ('power cable','023'), ('power cable','024')])
def test_multiple_standards_require_stored_requirements(database, product, code):
    _, sessions = database
    with sessions() as session:
        standard = StandardRepository(session).get_by_code('IS-DEMO-' + code)
        extraction = ExtractedInput(product=product)
        result = analyze_gaps('description', extraction, 'english', standard)
        assert result.total_checks == len(standard.requirements) and result.coverage_percentage == 0
        standard.requirements.clear()
        result = analyze_gaps('description', extraction, 'english', standard)
        assert result.status == 'not_assessed' and result.coverage_percentage is None
