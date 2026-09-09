from pydantic import BaseModel, Field, AliasChoices, field_validator
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

    @property
    def document_text(self) -> str:
        return clean_text(f"Standard: {self.id}\nTitle: {self.title}\nScope: {self.scope}\nAbstract: {self.abstract}\nKeywords: {', '.join(self.keywords)}")


class RecommendationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=50)

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
    supporting_evidence: list[str]
    validity: str = "unverified"


class RecommendationResponse(BaseModel):
    query: str
    recommendations: list[Recommendation]
    warnings: list[str] = Field(default_factory=lambda: [
        "Scores are uncalibrated relevance scores, not probabilities.",
        "Status and revision are dataset metadata, not verification of current validity. Human review is required.",
    ])
