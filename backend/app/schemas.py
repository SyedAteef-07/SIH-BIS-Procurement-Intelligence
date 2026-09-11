"""Public API schemas shared by the FastAPI routes and clients."""

import re
from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    embedding_mode: Literal["english", "multilingual"] = "english"
    description: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Product, specification, or tender text",
    )
    limit: int = Field(default=5, ge=1, le=20)

    @field_validator("description")
    @classmethod
    def meaningful_text(cls, value):
        # Keep Devanagari/Kannada combining signs attached to their words.
        if not any(len(term) > 2 for term in re.findall(r"[\w\u0900-\u097f\u0c80-\u0cff]+", value)):
            raise ValueError("description must contain at least one meaningful word")
        return value.strip()


class StandardSummary(BaseModel):
    number: str
    title: str
    scope: str
    edition: str | None = None
    status: str
    standard_code: str
    revision: str | None = None
    is_mock: bool = True
    validity: str = "unverified"
    abstract: str = ""
    publication_date: date | None = None
    withdrawn_date: date | None = None
    superseded_by: str | None = None
    source_url: str | None = None


class StandardDetail(StandardSummary):
    keywords: list[str] = Field(default_factory=list)
    related: list[str] = Field(default_factory=list)
    certification: str | None = None
    requirements: list[str] = Field(default_factory=list)


class Recommendation(StandardDetail):
    relevance_label: str = "Recommended"
    matched_terms: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    retrieval_score: float = Field(allow_inf_nan=False)
    reranker_score: float | None = Field(allow_inf_nan=False)
    retrieval_score_type: Literal["cosine", "rrf"]


class AnalysisResponse(BaseModel):
    embedding_mode: Literal["english", "multilingual"] = "english"
    detected_language: Literal["english", "hindi", "kannada"] = "english"
    reranking_applied: bool = True
    input: str
    recommendations: list[Recommendation]
    related_standards: list[Recommendation]
    certifications: list[str]
    gaps: list[str]
    explanation: str
    recommendation_source: Literal["ai_service"] = "ai_service"
    match_status: Literal["NOT_ASSESSED", "MATCH", "NO_RELIABLE_MATCH"]
    ai_match_status: Literal["NOT_ASSESSED", "MATCH", "NO_RELIABLE_MATCH"]
    has_reliable_match: bool | None = None
    warnings: list[str] = Field(default_factory=list)
    degraded: bool = False
    missing_standard_codes: list[str] = Field(default_factory=list)
