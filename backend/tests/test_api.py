from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_and_catalog():
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/api/standards", params={"search": "helmet"})
    assert response.status_code == 200
    assert response.json()[0]["number"] == "IS 15644:2006"


def test_analysis_returns_related_standards_and_certification():
    response = client.post(
        "/api/analyze",
        json={"description": "53 grade cement for concrete construction", "limit": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"][0]["number"] == "IS 12269:2013"
    assert "BIS Product Certification (Scheme-I)" in body["certifications"]
    assert "IS 4031 (Parts 1-15)" in [item["number"] for item in body["related_standards"]]


def test_analysis_rejects_empty_meaningful_input():
    response = client.post("/api/analyze", json={"description": "a b"})
    assert response.status_code == 422
