from app.nlp.extractor import RequirementExtractor


def test_pipe_details_and_negation():
    result = RequirementExtractor().extract('PVC water pipe 100 mm diameter PN 10 rubber ring joints for potable water. No 6 bar rating.')
    assert result.product == 'PVC water pipe'
    assert result.pressure_ratings == ['pn 10']
    assert result.joints == ['rubber ring joints']
    assert result.water_use == ['potable water']
    assert result.evidence['pressure_ratings'][-1].negated


def test_bare_numbers_do_not_become_pressure():
    assert not RequirementExtractor().extract('Order 100 PVC water pipes').pressure_ratings


def test_recommend_api_exposes_source_extraction():
    from fastapi.testclient import TestClient
    from app.main import create_app
    from test_quality_api import make_engine
    with TestClient(create_app(make_engine())) as client:
        body = client.post('/recommend', json={'text': 'PVC pipes for potable water at 10 bar'}).json()
    extracted = body['extracted_requirements']
    assert extracted['product'] == 'PVC water pipe'
    assert extracted['evidence']['pressure_ratings'][0]['evidence'] == '10 bar'
