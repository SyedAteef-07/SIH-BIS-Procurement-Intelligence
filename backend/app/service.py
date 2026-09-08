"""Recommendation and explainability logic for procurement specifications."""

import re
from dataclasses import asdict

from .catalog import BY_NUMBER, STANDARDS, Standard


def _terms(text: str) -> set[str]:
    return {term for term in re.findall(r"[\w]+", text.casefold()) if len(term) > 2}


def _standard_result(standard: Standard, score: float, matched: set[str]) -> dict:
    result = asdict(standard)
    result["keywords"] = list(standard.keywords)
    result["related"] = list(standard.related)
    result["requirements"] = list(standard.requirements)
    result["score"] = round(min(score, 1.0), 3)
    result["matched_terms"] = sorted(matched)
    return result


def _resolve_related(identifier: str) -> Standard | None:
    """Resolve references that omit an edition suffix (for example, ``IS 732``)."""
    if identifier in BY_NUMBER:
        return BY_NUMBER[identifier]
    return next(
        (
            standard
            for standard in STANDARDS
            if standard.number.startswith(f"{identifier}:")
            or standard.number.startswith(f"{identifier} (")
        ),
        None,
    )


def recommend(text: str, limit: int = 5) -> dict:
    query_terms = _terms(text)
    if not query_terms:
        raise ValueError("description must contain at least one meaningful word")

    ranked: list[tuple[float, Standard, set[str]]] = []
    for standard in STANDARDS:
        searchable = _terms(" ".join((standard.title, standard.scope, *standard.keywords)))
        matched = query_terms & searchable
        if matched:
            score = len(matched) / max(len(query_terms), 1)
            # A title hit is stronger than a generic scope/keyword hit.
            title_terms = _terms(standard.title)
            score += 0.25 * len(matched & title_terms) / max(len(title_terms), 1)
            ranked.append((score, standard, matched))

    ranked.sort(key=lambda item: item[0], reverse=True)
    recommendations = [_standard_result(item[1], item[0], item[2]) for item in ranked[:limit]]
    related_numbers = {number for item in ranked[:limit] for number in item[1].related}
    recommended_numbers = {item["number"] for item in recommendations}
    related = []
    for number in sorted(related_numbers):
        standard = _resolve_related(number)
        if standard and standard.number not in recommended_numbers:
            related.append(_standard_result(standard, 0.0, set()))

    requirements = sorted({requirement for item in recommendations for requirement in item["requirements"]})
    mentioned = {term.casefold() for term in query_terms}
    gaps = [requirement for requirement in requirements if not any(
        word in mentioned for word in _terms(requirement)
    )]
    return {
        "input": text,
        "recommendations": recommendations,
        "related_standards": related,
        "certifications": sorted({item["certification"] for item in recommendations if item["certification"]}),
        "gaps": gaps,
        "explanation": (
            (
                "No catalog concepts matched this input. Add product type, material, "
                "intended use, rating, or safety context and try again."
                if not recommendations
                else
                "Recommendations are ranked from overlapping product, scope, and multilingual "
                "concepts. Verify the cited edition and certification notification before issuing "
                "a tender."
            )
        ),
    }
