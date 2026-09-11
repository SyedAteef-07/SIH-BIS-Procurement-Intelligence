"""Validated HTTP boundary. Never import AI models into the orchestration API."""
from typing import Literal
import httpx
from pydantic import BaseModel, Field, ValidationError, model_validator
from app.config import settings
from app.services.gap_analysis import ExtractedInput


class AIServiceError(Exception):
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.status_code = status_code


class CandidateStandard(BaseModel):
    id: str = Field(min_length=1)
    is_mock: bool = False


class Candidate(BaseModel):
    standard: CandidateStandard
    retrieval_score: float = Field(allow_inf_nan=False)
    reranker_score: float | None = Field(allow_inf_nan=False)
    retrieval_score_type: Literal["cosine", "rrf"]
    supporting_evidence: list[str]
    validity: str = "unverified"


class AIResponse(BaseModel):
    extracted_requirements: ExtractedInput | None = None
    embedding_mode: Literal["english", "multilingual"] = "english"
    detected_language: Literal["english", "hindi", "kannada"] = "english"
    reranking_applied: bool = True
    recommendations: list[Candidate] = Field(max_length=50)
    match_status: Literal["NOT_ASSESSED", "MATCH", "NO_RELIABLE_MATCH"]
    has_reliable_match: bool | None = None
    warnings: list[str] = Field(default_factory=list)
    warning: str | None = None

    @model_validator(mode="after")
    def consistent(self):
        if self.reranking_applied and any(c.reranker_score is None for c in self.recommendations):
            raise ValueError("Missing scores for applied reranking")
        codes = [r.standard.id for r in self.recommendations]
        if len(codes) != len(set(codes)):
            raise ValueError("Duplicate AI identifiers")
        if self.match_status == "NO_RELIABLE_MATCH" and self.recommendations:
            raise ValueError("No-match response contains candidates")
        if self.match_status == "MATCH" and not self.recommendations:
            raise ValueError("Match response has no candidates")
        return self


class AIClient:
    def __init__(self, base_url=None, timeout=None, transport=None):
        self.base_url = (base_url or settings.ai_service_url).rstrip("/")
        self.timeout = settings.ai_timeout_seconds if timeout is None else timeout
        self.transport = transport

    async def _request(self, method, path, **kwargs):
        try:
            async with httpx.AsyncClient(base_url=self.base_url + "/", timeout=self.timeout,
                                         transport=self.transport, follow_redirects=False) as client:
                response = await client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            raise AIServiceError("AI service timed out; please try again", 504) from exc
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 422:
                raise AIServiceError("AI service could not process this requirement; try shorter, more specific text", 422) from exc
            raise AIServiceError("AI service is unavailable" if status >= 500 else "AI service returned an unexpected response", 503 if status >= 500 else 502) from exc
        except httpx.RequestError as exc:
            raise AIServiceError("AI service is unavailable", 503) from exc
        except ValueError as exc:
            raise AIServiceError("AI service returned invalid JSON", 502) from exc

    async def recommend(self, text, top_k, embedding_mode=None):
        body = {"text": text, "top_k": top_k}
        if embedding_mode is not None:
            body["embedding_mode"] = embedding_mode
        payload = await self._request("POST", "recommend", json=body)
        try:
            result = AIResponse.model_validate(payload)
            if embedding_mode is not None and result.embedding_mode != embedding_mode:
                raise ValueError("AI response used a different embedding mode")
            if len(result.recommendations) > top_k:
                raise ValueError("Too many candidates")
            return result
        except (ValidationError, ValueError) as exc:
            raise AIServiceError("AI service returned an invalid recommendation response", 502) from exc

    async def ready(self):
        payload = await self._request("GET", "ready")
        if not isinstance(payload, dict) or payload.get("status") != "ready":
            raise AIServiceError("AI service is not ready")
        return True


def get_ai_client():
    return AIClient()
