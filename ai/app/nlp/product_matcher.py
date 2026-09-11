"""Explicit aliases only; no similarity-based product guessing."""
import re
from app.nlp.technical_patterns import is_negated
from app.schemas.requirements import EvidenceItem

DEFAULT_ALIASES = {
    "distribution transformer": ["distribution transformer", "step down transformer"],
    "power transformer": ["power transformer"],
    "dry-type transformer": ["dry type transformer", "dry transformer", "cast resin transformer"],
    "instrument transformer": ["instrument transformer", "current transformer", "voltage transformer"],
    "transformer insulating oil": ["transformer insulating oil", "insulating oil", "transformer oil"],
    "transformer bushing": ["transformer bushing"],
    "transformer test methods": ["transformer test methods", "transformer testing"],
    "solid electrical insulation": ["solid electrical insulation", "solid dielectric sheet"],
    "street luminaire": ["street light", "street lighting fixture", "road luminaire", "roadway lighting fixture", "road lighting fixture", "LED road luminaire"],
    "indoor luminaire": ["indoor LED luminaire", "indoor luminaire", "ceiling LED panel", "LED ceiling panel"],
    "emergency lighting": ["emergency lighting", "emergency lighting unit", "emergency light"],
    "road lighting design": ["road lighting design"],
    "outdoor luminaire safety": ["outdoor luminaire safety"],
    "luminaire enclosure": ["luminaire enclosure", "lighting enclosure", "luminaire housing"],
    "power cable": ["power cable", "electrical cable", "insulated power cable", "low voltage PVC cable", "high voltage XLPE cable"],
    "circuit breaker": ["circuit breaker", "MCB", "MCCB"],
    "switchgear": ["switchgear", "switchgear assembly", "switchgear assemblies", "switchboard"],
    "earthing system": ["earthing system", "earth electrode", "grounding system"],
    "surge protective device": ["surge protective device", "surge protector"],
    "induction motor": ["induction motor"],
    "Portland cement": ["Portland cement"],
    "reinforcing bar": ["reinforcing bar", "reinforcement bar", "rebar"],
    "structural steel": ["structural steel", "steel beam", "steel column"],
    "concrete block": ["concrete block", "concrete masonry block"],
    "safety helmet": ["safety helmet", "protective headgear", "protective headwear", "industrial helmet", "industrial protective helmet"],
    "protective footwear": ["protective footwear", "safety footwear", "safety boot"],
    "insulating glove": ["insulating glove"],
    "PVC water pipe": ["PVC water pipe", "plastic pressure pipe", "PVC pressure pipe", "PVC water supply pipe"],
    "pump": ["pump", "water pump", "centrifugal pump", "centrifugal water pump"],
    "pump mechanical seal": ["pump mechanical seal", "pump seal", "mechanical shaft seal"],
    "water valve": ["water valve", "water pipeline valve", "gate valve", "check valve"],
    "water storage tank": ["water storage tank", "water tank"],
    "water meter": ["water meter", "water flow meter"],
    "drinking water quality": ["drinking water quality", "potable water quality"],
    "water purification unit": ["water purification unit", "water purification", "water treatment unit"],
    "fire extinguisher": ["fire extinguisher"],
    "fire hose": ["fire hose", "fire hose assembly", "fire hose assemblies"],
}


class ProductMatcher:
    def __init__(self, aliases=None):
        aliases = DEFAULT_ALIASES if aliases is None else aliases
        self.patterns = []
        for canonical, phrases in aliases.items():
            if not canonical.strip() or not phrases:
                raise ValueError("Product aliases require a name and phrases")
            for phrase in phrases:
                if not phrase.strip():
                    raise ValueError("Product alias must not be empty")
                words = re.split(r"[\s-]+", phrase.strip())
                expression = r"[\s\-\u2010-\u2015]+".join(re.escape(word) for word in words)
                # Explicit singular aliases also recognize an ordinary trailing s.
                self.patterns.append((canonical, re.compile(r"(?<!\w)" + expression + r"s?(?!\w)", re.IGNORECASE)))

    def find_matches(self, text):
        matches = []
        for canonical, pattern in self.patterns:
            for match in pattern.finditer(text):
                if not is_negated(text, match.start(), match.end()):
                    matches.append(EvidenceItem(value=canonical, evidence=match.group(), start=match.start(), end=match.end()))
        # Longer explicit phrases suppress generic matches inside their spans.
        selected = []
        for item in sorted(matches, key=lambda m: (-(m.end - m.start), m.start, m.value)):
            if not any(item.start < previous.end and item.end > previous.start for previous in selected):
                selected.append(item)
        return sorted(selected, key=lambda m: (m.start, m.value))

    def match(self, text):
        matches = self.find_matches(text)
        # A singular product is unsafe if the query explicitly names multiple products.
        return matches[0] if matches and len({m.value for m in matches}) == 1 else None
