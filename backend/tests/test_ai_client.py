import asyncio
import json
import httpx
import pytest
from app.services.ai_client import AIClient, AIServiceError
from conftest import ai_payload


def test_http_boundary_success():
    def respond(request):
        assert str(request.url) == "http://ai.test/base/recommend"
        assert json.loads(request.content) == {"text": "water pump", "top_k": 3}
        return httpx.Response(200, json=ai_payload())
    client = AIClient("http://ai.test/base", transport=httpx.MockTransport(respond))
    assert asyncio.run(client.recommend("water pump", 3)).recommendations[0].reranker_score == 7.91


@pytest.mark.parametrize("failure,status", [("timeout", 504), ("connection", 503), (503, 503), (422, 422), (404, 502), (302, 502), ("bad_json", 502), ("bad_schema", 502)])
def test_http_failures_do_not_leak_tender_text(failure, status, caplog):
    calls = []
    def respond(request):
        calls.append(request)
        if failure == "timeout":
            raise httpx.ReadTimeout("secret tender", request=request)
        if failure == "connection":
            raise httpx.ConnectError("secret tender", request=request)
        if failure == "bad_json":
            return httpx.Response(200, text="secret tender")
        if failure == "bad_schema":
            return httpx.Response(200, json={"error": "secret tender"})
        return httpx.Response(failure, json={"detail": "secret tender"})
    with pytest.raises(AIServiceError) as exc:
        asyncio.run(AIClient(transport=httpx.MockTransport(respond)).recommend("secret tender", 1))
    assert exc.value.status_code == status
    assert "secret tender" not in str(exc.value) and "secret tender" not in caplog.text
    assert len(calls) == 1


@pytest.mark.parametrize("payload", [ai_payload(("IS-DEMO-001", "IS-DEMO-001")), ai_payload(match_status="NO_RELIABLE_MATCH"), {"recommendations": [], "match_status": "MATCH"}])
def test_inconsistent_ai_responses_are_rejected(payload):
    client = AIClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=payload)))
    with pytest.raises(AIServiceError, match="invalid recommendation"):
        asyncio.run(client.recommend("pump", 5))
