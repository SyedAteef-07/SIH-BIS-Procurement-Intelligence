"""Public API schemas shared by the FastAPI routes and clients."""

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=3,
        max_length=50_000,
        description="Product, specification, or tender text",
    )
    limit: int = Field(default=5, ge=1, le=20)


class StandardSummary(BaseModel):
    number: str
    title: str
    scope: str
    edition: str
    status: str


class StandardDetail(StandardSummary):
    keywords: list[str]
    related: list[str]
    certification: str | None
    requirements: list[str]


class Recommendation(StandardDetail):
    score: float = Field(ge=0, le=1)
    matched_terms: list[str]


class AnalysisResponse(BaseModel):
    input: str
    recommendations: list[Recommendation]
    related_standards: list[Recommendation]
    certifications: list[str]
    gaps: list[str]
    explanation: str
