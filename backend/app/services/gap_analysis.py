"""Specification coverage prompts, never normative compliance verdicts.

Profiles are deliberately limited to identified products and demo records.
Each check must also be supported by the current database scope or abstract.
"""
import re
from typing import Literal
from pydantic import BaseModel, Field


class ExtractedEvidence(BaseModel):
    evidence: str
    value: str = ""
    negated: bool = False


class ExtractedInput(BaseModel):
    product: str | None = None
    evidence: dict[str, list[ExtractedEvidence]] = Field(default_factory=dict)


class GapCheck(BaseModel):
    label: str
    status: Literal["mentioned", "missing", "needs_review"]
    evidence: list[str]
    source_evidence: str
    action: str


class GapAnalysis(BaseModel):
    status: Literal["assessed", "not_assessed"] = "not_assessed"
    summary: str = "Requirement extraction was not supplied by the AI service. Restart the updated AI service and analyze again."
    scope: str = "Only the submitted text was checked. A mention is not proof that a specification is adequate or compliant."
    standard_code: str | None = None
    checks: list[GapCheck] = Field(default_factory=list)


# (extraction field, UI label, metadata topic, clarification prompt)
PROFILES = {
    ("PVC water pipe", "IS-DEMO-010"): [
        ("dimensions", "Pipe dimensions", r"dimensions", "Specify pipe diameter and wall thickness or dimension class."),
        ("pressure_ratings", "Pressure rating", r"pressure", "Specify the required operating pressure or pressure class."),
        ("joints", "Joint type", r"joints", "Specify the joint or connection type."),
        ("water_use", "Water application", r"potable|drinking", "Clarify whether the pipe is intended for potable water."),
    ],
    ("distribution transformer", "IS-DEMO-001"): [
        ("voltages", "Voltage ratings", r"voltage|kV", "Specify the required primary and secondary voltages."),
        ("power_ratings", "Power rating", r"ratings", "Specify the required transformer capacity in kVA or MVA."),
        ("phase", "Phase configuration", r"phase", "Specify the required phase configuration."),
        ("frequencies", "Frequency", r"Hz", "Specify the operating frequency."),
        ("installation", "Installation environment", r"outdoor", "Specify the installation environment."),
    ],
    ("power cable", "IS-DEMO-005"): [
        ("materials", "Conductor and insulation materials", r"copper|aluminium", "Specify conductor and insulation materials."),
        ("testing_requirements", "Testing requirements", r"testing", "Specify the required insulation tests and acceptance criteria."),
    ],
}


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
    rules = PROFILES.get((extracted.product, primary.standard_code))
    if not rules:
        result.summary = "No supported specification checklist matches both the identified product and primary recommendation. Refine the product description or review manually."
        return result
    for field, label, topic, action in rules:
        source = next((s for s in (primary.scope, primary.abstract) if s and re.search(topic, s, re.I)), None)
        if source is None:
            continue
        # Evidence must occur in the analyzed text; do not trust orphaned snippets.
        matches = [e for e in extracted.evidence.get(field, []) if e.evidence and e.evidence in text]
        state = "needs_review" if any(e.negated for e in matches) else "mentioned" if matches else "missing"
        result.checks.append(GapCheck(label=label, status=state,
            evidence=list(dict.fromkeys(e.evidence for e in matches)), source_evidence=source,
            action="Explicit exclusion or conflicting wording detected. Confirm the intended requirement." if state == "needs_review" else
                   "Detail mentioned; verify values and acceptance criteria manually." if state == "mentioned" else action))
    if not result.checks:
        result.summary = "The database metadata does not support the configured specification checks."
        return result
    result.status = "assessed"
    result.standard_code = primary.standard_code
    count = sum(c.status != "mentioned" for c in result.checks)
    result.summary = f"{count} potential specification gap(s) across {len(result.checks)} topic checks. Based on fictional demo metadata; these are clarification prompts, not BIS requirements or compliance findings."
    return result
