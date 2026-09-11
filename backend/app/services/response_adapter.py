"""Metadata is database-owned; candidate ordering is AI-owned."""
from app.database.repositories.standards import StandardRepository
from app.services.gap_analysis import analyze_gaps


def standard_detail(standard):
    mock = standard.is_mock or standard.standard_code.startswith("IS-DEMO-")
    return dict(number=standard.standard_code, standard_code=standard.standard_code,
                title=standard.title, scope=standard.scope, abstract=standard.abstract,
                edition=standard.revision, revision=standard.revision,
                status="unverified" if mock else standard.status, is_mock=mock,
                validity="unverified", publication_date=standard.publication_date,
                withdrawn_date=standard.withdrawn_date, superseded_by=standard.superseded_by,
                source_url=standard.source_url, keywords=[k.keyword for k in standard.keywords],
                related=[], certification=None, requirements=[])


def adapt_analysis(text, ai_response, session):
    codes = [c.standard.id for c in ai_response.recommendations]
    metadata = StandardRepository(session).get_by_codes(codes)
    missing = [code for code in codes if code not in metadata]
    warnings = list(ai_response.warnings)
    if ai_response.warning:
        warnings.append(ai_response.warning)
    recommendations = []
    for candidate in ai_response.recommendations:
        standard = metadata.get(candidate.standard.id)
        if standard is None:
            continue
        item = standard_detail(standard)
        if candidate.standard.is_mock:
            item.update(is_mock=True, status="unverified")
        item.update(relevance_label="Recommended", supporting_evidence=candidate.supporting_evidence,
                    retrieval_score=candidate.retrieval_score, reranker_score=candidate.reranker_score,
                    retrieval_score_type=candidate.retrieval_score_type)
        recommendations.append(item)
    warnings.append("Relevance scores are uncalibrated, not probabilities. Metadata validity has not been verified.")
    if any(item["is_mock"] for item in recommendations):
        warnings.append("Fictional IS-DEMO development metadata; these are not official BIS standards.")
    if missing:
        warnings.append("Some AI identifiers are missing from the metadata database; results are incomplete. Check the dataset and seed version.")
    analysis = analyze_gaps(text, ai_response.extracted_requirements, ai_response.detected_language,
                            metadata.get(codes[0]) if codes else None)
    extracted = ai_response.extracted_requirements
    details = list(dict.fromkeys(e.evidence for entries in extracted.evidence.values() for e in entries
                               if not e.negated and e.evidence and e.evidence in text)) if extracted else []
    return dict(input=text, recommendations=recommendations, related_standards=[], certifications=[],
                gaps=[f"{c.label}: {c.action}" for c in analysis.checks if c.status != "mentioned"],
                gap_analysis=analysis.model_dump(), extracted_requirements=details,
                embedding_mode=ai_response.embedding_mode, detected_language=ai_response.detected_language,
                reranking_applied=ai_response.reranking_applied,
                explanation="AI service ranking enriched with database metadata. " + analysis.summary + " Related/normative relationships and certification obligations have not been verified.",
                recommendation_source="ai_service", degraded=bool(missing), missing_standard_codes=missing,
                match_status="NOT_ASSESSED" if missing else ai_response.match_status,
                ai_match_status=ai_response.match_status,
                has_reliable_match=None if missing else ai_response.has_reliable_match,
                warnings=list(dict.fromkeys(warnings)))
