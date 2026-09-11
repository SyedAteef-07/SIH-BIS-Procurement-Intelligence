import asyncio
import json
import httpx
import pytest
from app.services.ai_client import AIClient, AIServiceError, get_ai_client
from app.main import app
from conftest import ai_payload


def multilingual_payload():
    payload = ai_payload(embedding_mode="multilingual", detected_language="hindi", reranking_applied=False)
    payload["recommendations"][0]["reranker_score"] = None
    payload["recommendations"][0]["retrieval_score_type"] = "cosine"
    return payload


@pytest.mark.parametrize("query,language", [("सीमेंट निर्माण", "hindi"), ("33 ಕೆವಿ ಪವರ್ ಕೇಬಲ್", "kannada")])
def test_backend_passes_mode_and_preserves_skipped_reranker(api, query, language):
    client, _ = api
    def respond(request):
        sent = json.loads(request.content)
        assert sent["embedding_mode"] == "multilingual" and sent["text"] == query
        payload = multilingual_payload()
        payload["detected_language"] = language
        return httpx.Response(200, json=payload)
    app.dependency_overrides[get_ai_client] = lambda: AIClient(transport=httpx.MockTransport(respond))
    body = client.post("/api/analyze", json={"description": query, "embedding_mode": "multilingual"}).json()
    assert body["embedding_mode"] == "multilingual" and body["detected_language"] == language
    assert body["reranking_applied"] is False
    assert body["recommendations"][0]["reranker_score"] is None
    assert body["recommendations"][0]["is_mock"]
    assert client.post("/api/analyze", json={"description": "cement", "embedding_mode": "bad"}).status_code == 422


def test_service_cannot_silently_use_wrong_mode():
    client = AIClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=ai_payload())))
    with pytest.raises(AIServiceError):
        asyncio.run(client.recommend("पावर केबल", 5, embedding_mode="multilingual"))
