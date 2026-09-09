from typing import Literal
from pydantic import BaseModel, Field, AliasChoices, field_validator
from app.config import DEFAULT_FINAL_K
from app.nlp.preprocess import clean_text


class Standard(BaseModel):
    id: str = Field(min_length=1, validation_alias=AliasChoices("id", "standard_id"))
    title: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)
    abstract: str = ""
    status: str | None = None
    revision: str | None = None
    source: str | None = None
    is_mock: bool = False

    def to_retrieval_text(self) -> str:
        parts = [self.title, self.scope, self.abstract, " ".join(self.keywords)]
        return clean_text(". ".join(part.strip().rstrip(".") for part in parts if part.strip()))

    @property
    def document_text(self) -> str:
        """Compatibility alias; all retrievers use the same content-only text."""
        return self.to_retrieval_text()


class RecommendationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=DEFAULT_FINAL_K, ge=1, le=50)

    @field_validator("text")
    @classmethod
    def meaningful_text(cls, value):
        value = clean_text(value)
        if not value:
            raise ValueError("Text must contain a procurement requirement")
        return value


class Recommendation(BaseModel):
    standard: Standard
    retrieval_score: float
    reranker_score: float
    retrieval_score_type: Literal["cosine", "rrf"] = "cosine"
    supporting_evidence: list[str]
    validity: str = "unverified"


class RecommendationResponse(BaseModel):
    query: str
    recommendations: list[Recommendation]
    has_reliable_match: bool | None = None
    match_status: Literal["NOT_ASSESSED", "MATCH", "NO_RELIABLE_MATCH"] = "NOT_ASSESSED"
    warning: str | None = None
    warnings: list[str] = Field(default_factory=lambda: [
        "Scores are uncalibrated relevance scores, not probabilities.",
        "Status and revision are dataset metadata, not verification of current validity. Human review is required.",
    ])
