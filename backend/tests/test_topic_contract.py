import json
import subprocess
import sys
from pathlib import Path
import pytest
from sqlalchemy import func, select
from app.database.models import StandardRelationship, StandardCertification, StandardRequirement
from app.database.repositories.standards import StandardRepository
from app.scripts.seed_standards import seed_standards, FIXTURE
from conftest import ai_payload

CASES = [
    ('002', 'Portland cement compressive strength setting time soundness for concrete construction', 100),
    ('002', 'Portland cement compressive strength for concrete construction', 50),
    ('004', 'industrial safety helmet with impact protection and penetration resistance', 75),
    ('008', 'centrifugal water pump flow rate 100 lpm, head 20 m, hydraulic efficiency', 100),
]

@pytest.fixture(scope='module')
def extracted_cases():
    # Run the real lightweight extractor in its own process to avoid the two
    # services' app package-name collision. No embedding model or network used.
    script = "import json,sys; from app.nlp.extractor import RequirementExtractor; print(json.dumps([RequirementExtractor().extract(t).model_dump() for t in json.load(sys.stdin)]))"
    process = subprocess.run([sys.executable, '-c', script], cwd=FIXTURE.parents[1],
        input=json.dumps([text for _, text, _ in CASES]), text=True, capture_output=True, check=True, timeout=30)
    return json.loads(process.stdout)

@pytest.mark.parametrize('index', range(len(CASES)))
def test_actual_extraction_survives_boundary_and_covers_stored_topics(api, extracted_cases, index):
    code, text, percentage = CASES[index]
    client, ai = api
    ai.payload = ai_payload(('IS-DEMO-' + code,), extracted_requirements=extracted_cases[index])
    response = client.post('/api/analyze', json={'description': text})
    assert response.status_code == 200
    analysis = response.json()['gap_analysis']
    assert analysis['coverage_percentage'] == percentage
    assert analysis['total_checks'] == 4
    checks = {c['requirement_key']: c['status'] for c in analysis['checks']}
    if index == 1:
        assert checks == dict(compressive_strength='mentioned', construction_use='mentioned', setting_time='missing', soundness='missing')
    if index == 2:
        assert checks['impact_protection'] == checks['penetration_resistance'] == 'mentioned'
        assert checks['retention'] == 'missing'
    if index == 3:
        assert all(checks[k] == 'mentioned' for k in ['flow', 'head', 'hydraulic_efficiency', 'water_application'])

def test_seed_metadata_is_json_owned_and_idempotent(database, tmp_path):
    _, sessions = database
    rows = json.loads(FIXTURE.read_text())
    rows[0]['related_standards'][0]['relationship_type'] = 'custom_fixture_type'
    rows[0]['certifications'][0].update(name='Fixture certification', authority='Fixture authority', note='Fixture verification note.', status='verified', applicable=True)
    path = tmp_path / 'standards.json'
    path.write_text(json.dumps(rows))
    with sessions.begin() as session:
        for _ in range(2):
            seed_standards(session, path)
        assert session.scalar(select(func.count()).select_from(StandardRelationship)) == 15
        assert session.scalar(select(func.count()).select_from(StandardCertification)) == 5
        assert session.scalar(select(func.count()).select_from(StandardRequirement)) == sum(len(r.get('requirements', [])) for r in rows)
        standard = StandardRepository(session).get_by_code(rows[0]['id'])
        assert any(r.relationship_type == 'custom_fixture_type' for r in standard.outgoing_relationships)
        cert = standard.certifications[0]
        assert cert.name == 'Fixture certification' and cert.note == 'Fixture verification note.'
        assert cert.status == 'unverified' and cert.applicable is None

def test_gap_engine_remains_generic():
    source = (Path(__file__).parents[1] / 'app/services/gap_analysis.py').read_text().lower()
    assert not any(term in source for term in ['is-demo-', 'profiles', 'portland', 'helmet', 'transformer', 'centrifugal'])
