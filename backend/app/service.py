"""Recommendation and explainability logic for procurement specifications."""

import re
from dataclasses import asdict

from .catalog import BY_NUMBER, STANDARDS, Standard
from .services import graph_service
from .config import settings
from .mock_catalog import load_mock_standards
_ALL_STANDARDS = STANDARDS + (load_mock_standards() if settings.include_mock_standards else ())

def _terms(text: str) -> set[str]:
    return {term for term in re.findall(r"[\w]+", text.casefold()) if len(term) > 2}


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
    
    # 1. Parse Requirements from query terms (dummy mock for extraction)
    requirements = [{"id": f"req-{i}", "text": term.capitalize(), "type": "keyword"} for i, term in enumerate(list(query_terms)[:5])]

    # 2. Recommended Standards
    recommended_standards = []
    for score, standard, matched in ranked[:limit]:
        relevance_score = round(min(score, 1.0), 3)
        recommended_standards.append({
            "id": standard.number,
            "number": standard.number,
            "title": standard.title,
            "relevanceScore": relevance_score,
            "status": standard.status,
            "reason": f"Matches {len(matched)} terms from your query including: {', '.join(list(matched)[:3])}."
        })

    # 3. Related Standards
    related_numbers = {number for item in ranked[:limit] for number in item[1].related}
    for item in ranked[:limit]:
        related_numbers.update(graph_service.related_numbers(item[1].number))
    
    recommended_numbers = {item["id"] for item in recommended_standards}
    related_standards = []
    for number in sorted(related_numbers):
        standard = _resolve_related(number)
        if standard and standard.number not in recommended_numbers:
            related_standards.append({
                "id": standard.number,
                "number": standard.number,
                "title": standard.title,
                "relevanceScore": 0.5,
                "status": standard.status,
                "reason": "Referenced as a normative or related standard."
            })

    # 4. Certifications
    certifications = []
    seen_certs = set()
    for item in ranked[:limit]:
        cert = item[1].certification
        if cert and cert not in seen_certs:
            seen_certs.add(cert)
            certifications.append({
                "name": cert,
                "applicable": True,
                "description": "Certification required as per QCO.",
                "authority": "Bureau of Indian Standards",
                "source": "BIS Official Notification"
            })

    # 5. Gap Analysis
    all_requirements = sorted({requirement for item in ranked[:limit] for requirement in item[1].requirements})
    mentioned = {term.casefold() for term in query_terms}
    
    gap_analysis = []
    for req in all_requirements:
        # If any word from the standard's requirement is in the query, we consider it covered.
        req_terms = _terms(req)
        if any(word in mentioned for word in req_terms):
            gap_analysis.append({
                "requirement": req,
                "coverage": "COVERED",
                "explanation": "This requirement was found in your query."
            })
        else:
            gap_analysis.append({
                "requirement": req,
                "coverage": "NOT_COVERED",
                "explanation": "This is typically required by the standard but not mentioned in your tender."
            })

    # 6. Recommendation
    if recommended_standards:
        best_match = recommended_standards[0]
        rec_info = {
            "text": f"We recommend {best_match['number']} as it is the most relevant standard for your procurement requirement.",
            "confidence": best_match['relevanceScore']
        }
        explanation = "Recommendations are ranked from overlapping product, scope, and multilingual concepts. Verify the cited edition and certification notification before issuing a tender."
    else:
        rec_info = {
            "text": "Insufficient evidence to make a reliable recommendation.",
            "confidence": 0.0
        }
        explanation = "No catalog concepts matched this input. Add product type, material, intended use, rating, or safety context and try again."

    # 7. Evidence
    evidence = []
    for score, standard, matched in ranked[:limit]:
        evidence.append({
            "id": f"ev-{standard.number}",
            "title": standard.title,
            "sourceType": "BIS Standard Scope",
            "excerpt": standard.scope,
            "sourceUrl": f"https://standardsbis.bsbedge.com/",
            "relevanceScore": round(min(score, 1.0), 3)
        })

    return {
        "query": text,
        "requirements": requirements,
        "recommendedStandards": recommended_standards,
        "relatedStandards": related_standards,
        "certifications": certifications,
        "gapAnalysis": gap_analysis,
        "recommendation": rec_info,
        "evidence": evidence,
        "explanation": explanation
    }
