"""Append supported facts without rewriting or truncating user intent."""
from app.nlp.preprocess import clean_text


class QueryBuilder:
    def build(self, text, requirements, *, token_count=None, max_tokens=None):
        original = clean_text(text)
        if requirements.cleaned_text != original:
            raise ValueError("Extraction must belong to the supplied query")
        lines = []
        if requirements.product:
            lines.append(f"Product: {requirements.product}.")
        for field, label in [("product_type", "Type"), ("materials", "Material"), ("phase", "Phase"),
                             ("voltages", "Voltage"), ("frequencies", "Frequency"), ("power_ratings", "Power rating"),
                             ("dimensions", "Dimension"), ("ip_ratings", "IP rating"), ("technical_classes", "Class"),
                             ("installation", "Installation"), ("environment", "Environment"),
                             ("testing_requirements", "Testing"), ("safety_requirements", "Safety"),
                             ("performance_requirements", "Performance"), ("installation_requirements", "Installation requirement"),
                             ("material_requirements", "Material requirement"), ("certification_requirements", "Certification requirement")]:
            values = getattr(requirements, field)
            if values:
                formatted = [v.replace("_", " ") if isinstance(v, str)
                             else f"{v.value:g} {v.unit}" + (f" {v.kind}" if v.kind else "") for v in values]
                lines.append(f"{label}: {', '.join(dict.fromkeys(formatted))}.")
        enriched = original
        for line in lines:
            candidate = enriched + "\n" + line
            if token_count is not None and max_tokens is not None and token_count(candidate) > max_tokens:
                break
            enriched = candidate
        return enriched
