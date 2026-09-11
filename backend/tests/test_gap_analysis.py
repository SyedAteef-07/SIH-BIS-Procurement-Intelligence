import pytest
from conftest import ai_payload


def payload(evidence=None, **kwargs):
    return ai_payload(("IS-DEMO-010",), extracted_requirements={
        "product": "PVC water pipe", "evidence": evidence or {}}, **kwargs)


def test_pipe_missing_and_present_details(api):
    client, ai = api
    ai.payload = payload({"water_use": [{"evidence": "potable water"}]})
    result = client.post('/api/analyze', json={"description": "PVC water pipe for potable water"}).json()
    analysis = result['gap_analysis']
    assert analysis['status'] == 'assessed'
    assert len(result['gaps']) == 3
    assert analysis['checks'][-1]['status'] == 'mentioned'
    assert all(c['source_evidence'] for c in analysis['checks'])
    assert result['extracted_requirements'] == ['potable water']
    assert result['certifications'] == []


def test_zero_gaps_is_assessed_and_negation_needs_review(api):
    client, ai = api
    evidence = {key: [{"evidence": value}] for key, value in
                [('dimensions', '100 mm'), ('pressure_ratings', '10 bar'), ('joints', 'rubber ring'), ('water_use', 'potable water')]}
    ai.payload = payload(evidence)
    text = 'PVC water pipe 100 mm 10 bar rubber ring for potable water'
    result = client.post('/api/analyze', json={'description': text}).json()
    assert result['gaps'] == [] and result['gap_analysis']['status'] == 'assessed'
    evidence['pressure_ratings'][0]['negated'] = True
    ai.payload = payload(evidence)
    result = client.post('/api/analyze', json={'description': text}).json()
    assert result['gap_analysis']['checks'][1]['status'] == 'needs_review'


@pytest.mark.parametrize('case', ['language', 'product', 'metadata', 'legacy', 'no_match'])
def test_unassessed_states(api, case):
    client, ai = api
    ai.payload = payload()
    if case == 'language': ai.payload['detected_language'] = 'hindi'
    if case == 'product': ai.payload['extracted_requirements']['product'] = None
    if case == 'metadata': ai.payload['recommendations'][0]['standard']['id'] = 'missing'
    if case == 'legacy': ai.payload.pop('extracted_requirements')
    if case == 'no_match': ai.payload.update(recommendations=[], match_status='NO_RELIABLE_MATCH')
    result = client.post('/api/analyze', json={'description': 'PVC water pipe'}).json()
    assert result['gap_analysis']['status'] == 'not_assessed'
    assert result['gaps'] == [] and result['gap_analysis']['summary']


def test_orphan_evidence_does_not_satisfy_check(api):
    client, ai = api
    ai.payload = payload({'pressure_ratings': [{'evidence': '10 bar'}]})
    result = client.post('/api/analyze', json={'description': 'PVC water pipe'}).json()
    assert result['gap_analysis']['checks'][1]['status'] == 'missing'


def test_truncated_pdf_limits_gap_scope(api):
    import pymupdf
    client, ai = api
    ai.payload = payload()
    with pymupdf.open() as document:
        for _ in range(4):
            page = document.new_page()
            page.insert_textbox(pymupdf.Rect(40, 40, 550, 800), 'PVC water pipe procurement requirement. ' * 25, fontsize=10)
        data = document.tobytes()
    response = client.post('/api/analyze-pdf', files={'file': ('tender.pdf', data, 'application/pdf')})
    assert response.status_code == 200
    assert len(response.json()['input']) == 2000
    assert 'first 2,000' in response.json()['gap_analysis']['scope']
