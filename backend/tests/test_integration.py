import pytest
from sqlalchemy import text
from app.services.ai_client import AIServiceError
from conftest import ai_payload


def test_ranking_metadata_evidence_and_uncalibrated_scores(api):
    client, ai = api
    ai.payload = ai_payload(("IS-DEMO-008", "IS-DEMO-001", "IS-DEMO-002"))
    body = client.post("/api/analyze", json={"description": "water pump"}).json()
    assert [r["number"] for r in body["recommendations"]] == ["IS-DEMO-008", "IS-DEMO-001", "IS-DEMO-002"]
    assert body["recommendations"][1]["title"] == "Distribution Transformers"
    assert all(r["is_mock"] and r["status"] == r["validity"] == "unverified" for r in body["recommendations"])
    assert body["recommendations"][0]["reranker_score"] == 7.91
    assert body["recommendations"][0]["supporting_evidence"] == ["Evidence from the retrieval fixture"]
    assert all("score" not in r and "confidence" not in r for r in body["recommendations"])
    assert body["recommendation_source"] == "ai_service" and not body["degraded"]
    assert body["match_status"] == "NOT_ASSESSED" and body["has_reliable_match"] is None


@pytest.mark.parametrize("codes", [("missing", "IS-DEMO-002"), ("missing",)])
def test_unknown_ids_are_not_fabricated(api, codes):
    client, ai = api
    ai.payload = ai_payload(codes, match_status="MATCH", has_reliable_match=True)
    body = client.post("/api/analyze", json={"description": "cement construction"}).json()
    assert body["degraded"] and body["missing_standard_codes"] == ["missing"]
    assert all(r["number"] != "missing" for r in body["recommendations"])
    assert body["match_status"] == "NOT_ASSESSED" and body["ai_match_status"] == "MATCH"
    assert body["has_reliable_match"] is None


@pytest.mark.parametrize("status", [503, 504, 502, 422])
def test_no_silent_heuristic_fallback(api, status):
    client, ai = api
    ai.error = AIServiceError("AI service unavailable", status)
    response = client.post("/api/analyze", json={"description": "cement construction"})
    assert response.status_code == status
    assert "recommendations" not in response.json()


def test_no_match_and_health_independent_of_dependencies(api, database):
    client, ai = api
    ai.payload = ai_payload((), match_status="NO_RELIABLE_MATCH", has_reliable_match=False)
    body = client.post("/api/analyze", json={"description": "office chair"}).json()
    assert body["match_status"] == "NO_RELIABLE_MATCH" and body["recommendations"] == []
    assert client.get("/ready").status_code == 200
    ai.error = AIServiceError("AI service unavailable")
    assert client.get("/ready").status_code == 503
    assert client.get("/health").status_code == 200
    engine, _ = database
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE standards RENAME TO unavailable_standards"))
    assert client.get("/ready").json()["dependencies"]["database"] is False
    assert client.get("/api/standards").status_code == 503
    assert client.get("/health").status_code == 200


def test_detail_unknown_and_long_input(api):
    client, ai = api
    assert client.get("/api/standards/IS-DEMO-001").json()["keywords"]
    assert client.get("/api/standards/missing").status_code == 404
    assert client.post("/api/analyze", json={"description": "a" * 2001}).status_code == 422
    assert not ai.calls
