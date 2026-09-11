"""Deterministic procurement extraction. Offsets refer to the supplied source."""
import re
from app.nlp import technical_patterns as patterns
from app.nlp.normalization import normalize_technical_value, normalize_phase, normalize_ip_rating, normalize_phrase
from app.nlp.preprocess import clean_text
from app.nlp.product_matcher import ProductMatcher
from app.schemas.requirements import ExtractedRequirements, EvidenceItem


class RequirementExtractor:
    def __init__(self, product_matcher=None):
        self.product_matcher = product_matcher or ProductMatcher()

    def extract(self, text: str) -> ExtractedRequirements:
        result = ExtractedRequirements(cleaned_text=clean_text(text))
        matches = self.product_matcher.find_matches(text)
        if matches:
            result.evidence["product"] = matches
        product = self.product_matcher.match(text)
        if product:
            result.product, result.product_evidence = product.value, product.evidence

        def add(field, match, value):
            negated = patterns.is_negated(text, match.start(), match.end())
            result.evidence.setdefault(field, []).append(EvidenceItem(
                value=str(value), evidence=match.group(), start=match.start(), end=match.end(), negated=negated))
            if not negated and value not in getattr(result, field):
                getattr(result, field).append(value)

        for field, pattern in [("voltages", patterns.VOLTAGE), ("frequencies", patterns.FREQUENCY),
                               ("power_ratings", patterns.POWER), ("dimensions", patterns.DIMENSION)]:
            for match in pattern.finditer(text):
                value = normalize_technical_value(match.group())
                value.start, value.end = match.span()
                if field == "dimensions" and (re.search(r"\bdiameter\s*(?:of\s*)?$", text[:match.start()], re.I)
                                               or re.match(r"\s*(?:in\s+)?diameter\b", text[match.end():], re.I)):
                    value.kind = "diameter"
                negated = patterns.is_negated(text, *match.span())
                result.evidence.setdefault(field, []).append(EvidenceItem(
                    value=f"{value.value} {value.unit}", evidence=match.group(), start=match.start(), end=match.end(), negated=negated))
                if not negated:
                    getattr(result, field).append(value)

        fields = [("pressure_ratings", re.compile(r"\b(?:\d+(?:\.\d+)?\s*(?:bar|MPa|psi)|PN\s*\d+)\b", re.I), normalize_phrase),
                  ("joints", re.compile(r"\b(?:solvent[ -]weld(?:ed)?|rubber[ -]ring|threaded|flanged|socket(?:ed)?)\s*(?:joints?|connections?)?\b", re.I), normalize_phrase),
                  ("water_use", re.compile(r"\b(?:potable|drinking)\s+water\b", re.I), normalize_phrase),
                  ("phase", patterns.PHASE, normalize_phase),
                  ("ip_ratings", patterns.IP_RATING, normalize_ip_rating),
                  ("technical_classes", patterns.TECHNICAL_CLASS, lambda s: "Class " + s[-1].upper()),
                  ("materials", patterns.MATERIAL, lambda s: s.upper() if s.lower() in {"pvc", "xlpe"} else s.lower().replace("aluminum", "aluminium")),
                  ("product_type", patterns.PRODUCT_TYPE, normalize_phrase),
                  ("installation", patterns.INSTALLATION, normalize_phrase),
                  ("environment", patterns.ENVIRONMENT, normalize_phrase),
                  ("safety_requirements", patterns.SAFETY, normalize_phrase),
                  ("performance_requirements", patterns.PERFORMANCE, normalize_phrase),
                  ("installation_requirements", patterns.INSTALLATION_REQUIREMENT, normalize_phrase),
                  ("material_requirements", patterns.MATERIAL_REQUIREMENT, normalize_phrase),
                  ("certification_requirements", patterns.CERTIFICATION, normalize_phrase)]
        for field, pattern, normalize in fields:
            for match in pattern.finditer(text):
                add(field, match, normalize(match.group()))
        for match in patterns.TESTING.finditer(text):
            for term in patterns.TEST_TERM.finditer(match.group("terms")):
                add("testing_requirements", match, normalize_phrase(term.group()) + " testing")
        return result
