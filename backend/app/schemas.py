from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class AnalyzeRequest(BaseModel):
    description: str = Field(..., min_length=3, max_length=50_000, description="Product, specification, or tender text")
    limit: int = Field(default=5, ge=1, le=20)

class Requirement(BaseModel):
    id: str
    text: str
    type: Optional[str] = None

class Standard(BaseModel):
    id: str
    number: str
    title: str
    relevanceScore: float
    status: str
    reason: Optional[str] = None

class GapItem(BaseModel):
    requirement: str
    coverage: Literal["COVERED", "PARTIAL", "NOT_COVERED"]
    explanation: Optional[str] = None

class Evidence(BaseModel):
    id: str
    title: str
    sourceType: Optional[str] = None
    excerpt: Optional[str] = None
    sourceUrl: Optional[str] = None
    relevanceScore: Optional[float] = None

class Certification(BaseModel):
    name: str
    applicable: bool
    description: Optional[str] = None
    authority: Optional[str] = None
    source: Optional[str] = None

class RecommendationInfo(BaseModel):
    text: str
    confidence: float

class AnalyzeResponse(BaseModel):
    query: str
    requirements: List[Requirement]
    recommendedStandards: List[Standard]
    relatedStandards: List[Standard]
    certifications: List[Certification]
    gapAnalysis: List[GapItem]
    recommendation: RecommendationInfo
    evidence: List[Evidence]
    explanation: str
