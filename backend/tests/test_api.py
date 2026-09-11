def test_health_and_catalog(api):
    client, _ = api
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/api/standards", params={"search": "helmet"})
    assert response.status_code == 200
    assert response.json()[0]["number"] == "IS-DEMO-004"
    assert response.json()[0]["is_mock"] is True


def test_analysis_returns_ranked_metadata_without_invented_certification(api):
    client, ai = api
    response = client.post(
        "/api/analyze",
        json={"description": "53 grade cement for concrete construction", "limit": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"][0]["number"] == "IS-DEMO-002"
    assert body["recommendations"][0]["title"] == "Portland Cement"
    assert body["certifications"] == [] and body["related_standards"] == []
    assert ai.calls == [("53 grade cement for concrete construction", 1)]


def test_analysis_rejects_empty_meaningful_input(api):
    client, ai = api
    response = client.post("/api/analyze", json={"description": "a b"})
    assert response.status_code == 422
    assert ai.calls == []
