"""Generic metadata-driven topic coverage, never a compliance verdict."""
from typing import Literal
from pydantic import BaseModel, Field


class ExtractedEvidence(BaseModel):
    evidence: str
    value: str = ""
    negated: bool = False
    conflicting: bool = False


class ExtractedInput(BaseModel):
    product: str | None = None
    evidence: dict[str, list[ExtractedEvidence]] = Field(default_factory=dict)


class GapCheck(BaseModel):
    requirement_key: str
    label: str
    requirement_description: str
    category: str | None = None
    is_mandatory: bool = True
    source_section: str | None = None
    status: Literal["mentioned", "missing", "needs_review"]
    evidence: list[str]
    source_evidence: str
    action: str


class GapAnalysis(BaseModel):
    coverage_percentage: float | None = None
    mentioned_count: int = 0
    total_checks: int = 0
    missing_count: int = 0
    needs_review_count: int = 0
    status: Literal["assessed", "not_assessed"] = "not_assessed"
    summary: str = "Requirement extraction was not supplied by the AI service. Restart the updated AI service and analyze again."
    scope: str = "Only the submitted text was checked. A mention is not proof that a specification is adequate or compliant."
    standard_code: str | None = None
    checks: list[GapCheck] = Field(default_factory=list)


def analyze_gaps(text, extracted, language, primary):
    result = GapAnalysis()
    if extracted is None:
        return result
    if language != "english":
        result.summary = "Specification checks currently support English text only. Multilingual retrieval results remain available."
        return result
    if primary is None:
        result.summary = "No primary standard with database metadata is available for specification checks."
        return result
    requirements = primary.requirements
    if not requirements:
        result.summary = "The primary standard has no requirement metadata; specification coverage was not assessed."
        return result
    for requirement in requirements:
        # Ignore orphaned snippets; evidence must belong to the analyzed input.
        matches = [e for e in extracted.evidence.get(requirement.requirement_key, [])
                   if e.evidence and e.evidence in text]
        positive = any(not e.negated and not e.conflicting for e in matches)
        state = "mentioned" if positive else "needs_review" if matches else "missing"
        result.checks.append(GapCheck(
            requirement_key=requirement.requirement_key, label=requirement.label,
            requirement_description=requirement.description, category=requirement.category,
            is_mandatory=requirement.is_mandatory, source_section=requirement.source_section,
            status=state, evidence=list(dict.fromkeys(e.evidence for e in matches)),
            source_evidence=requirement.source_section or requirement.description,
            action="Detail mentioned; verify values and acceptance criteria manually." if positive else
                   "Only excluded or conflicting wording was found. Confirm the intended requirement." if matches else
                   requirement.description))
    result.status = "assessed"
    result.standard_code = primary.standard_code
    result.total_checks = len(result.checks)
    result.mentioned_count = sum(c.status == "mentioned" for c in result.checks)
    result.missing_count = sum(c.status == "missing" for c in result.checks)
    result.needs_review_count = sum(c.status == "needs_review" for c in result.checks)
    result.coverage_percentage = round(result.mentioned_count / result.total_checks * 100, 2)
    count = result.missing_count + result.needs_review_count
    result.summary = f"{result.mentioned_count} of {result.total_checks} specification topics were mentioned ({result.coverage_percentage:g}% requirement coverage). {count} topic(s) need clarification. This is not a compliance verdict. Coverage describes topic mentions only; it does not establish standards compliance."
    return result
