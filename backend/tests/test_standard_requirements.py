import ast
import json
from pathlib import Path
from typing import get_args
import pytest
from sqlalchemy import select, func
from app.database.models import Standard, StandardRequirement
from app.database.repositories.standards import StandardRepository
from app.scripts.seed_standards import seed_standards, FIXTURE, DemoRequirement
from app.services.gap_analysis import analyze_gaps, ExtractedInput


@pytest.mark.parametrize('code,title', [('CUSTOM-A', 'Unknown equipment'), ('CUSTOM-B', 'Unlisted material')])
def test_generic_engine_without_product_or_identifier_rules(database, code, title):
    _, sessions = database
    with sessions.begin() as session:
        standard = Standard(standard_code=code, title=title, requirements=[
            StandardRequirement(requirement_key='voltages', label='Supply', description='Specify voltage.', source_section='Section 3', is_mandatory=False),
            StandardRequirement(requirement_key='materials', label='Material', description='Specify material.', source_section='Section 4'),
            StandardRequirement(requirement_key='frequencies', label='Frequency', description='Specify frequency.'),
        ])
        session.add(standard)
        session.flush()
        standard = StandardRepository(session).get_by_code(code)
        extraction = ExtractedInput.model_validate({'product': None, 'evidence': {
            'voltages': [{'evidence': '11 kV'}, {'evidence': '33 kV', 'negated': True}],
            'materials': [{'evidence': 'steel', 'negated': True}],
        }})
        result = analyze_gaps('11 kV, not 33 kV; no steel', extraction, 'english', standard)
        checks = {c.requirement_key: c for c in result.checks}
        assert result.coverage_percentage == 33.33
        assert (result.mentioned_count, result.missing_count, result.needs_review_count, result.total_checks) == (1, 1, 1, 3)
        assert checks['voltages'].status == 'mentioned'
        assert checks['voltages'].evidence == ['11 kV', '33 kV']
        assert checks['voltages'].requirement_description == 'Specify voltage.'
        assert checks['voltages'].source_evidence == 'Section 3'
        assert not checks['voltages'].is_mandatory
        assert checks['materials'].status == 'needs_review'
        assert checks['frequencies'].status == 'missing'
        extraction.evidence['voltages'][0].conflicting = True
        result = analyze_gaps('11 kV, not 33 kV; no steel', extraction, 'english', standard)
        assert result.coverage_percentage == 0 and result.needs_review_count == 2
        standard.requirements.clear()
        assert analyze_gaps('11 kV', extraction, 'english', standard).status == 'not_assessed'


def test_requirement_seeding_updates_removes_and_preserves_ids(database, tmp_path):
    _, sessions = database
    rows = json.loads(FIXTURE.read_text(encoding='utf-8-sig'))
    expected = sum(len(r.get('requirements', [])) for r in rows)
    path = tmp_path / 'fixture.json'
    with sessions.begin() as session:
        original = dict(session.execute(select(StandardRequirement.requirement_key, StandardRequirement.id).where(
            StandardRequirement.standard_id == StandardRepository(session).get_by_code('IS-DEMO-001').id)).all())
        seed_standards(session)
        seed_standards(session)
        assert session.scalar(select(func.count()).select_from(StandardRequirement)) == expected
        rows[0]['requirements'][0]['description'] = 'Updated description.'
        rows[0]['requirements'].pop()
        path.write_text(json.dumps(rows), encoding='utf-8')
        seed_standards(session, path)
        assert session.scalar(select(func.count()).select_from(StandardRequirement)) == expected - 1
        standard = StandardRepository(session).get_by_code('IS-DEMO-001')
        voltage = next(r for r in standard.requirements if r.requirement_key == 'voltages')
        assert voltage.id == original['voltages'] and voltage.description == 'Updated description.'


def test_seed_keys_match_actual_ai_schema_and_reject_bad_metadata(database, tmp_path):
    # Inspect the separate service contract without importing its app package.
    schema = FIXTURE.parents[1] / 'app/schemas/requirements.py'
    tree = ast.parse(schema.read_text(encoding='utf-8'))
    model = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ExtractedRequirements')
    fields = {n.target.id for n in model.body if isinstance(n, ast.AnnAssign)}
    assert set(get_args(DemoRequirement.model_fields['key'].annotation)) <= fields
    rows = json.loads(FIXTURE.read_text(encoding='utf-8-sig'))
    assert all(r['key'] in fields for row in rows for r in row.get('requirements', []))
    _, sessions = database
    for bad in ['unknown_key', rows[0]['requirements'][1]['key']]:
        rows[0]['requirements'][0]['key'] = bad
        path = tmp_path / 'bad.json'
        path.write_text(json.dumps(rows), encoding='utf-8')
        with sessions() as session, pytest.raises(ValueError):
            seed_standards(session, path)
