"""Explicit topic mentions for demo coverage; no inferred acceptance criteria."""
TOPIC_PATTERNS = {
    "compressive_strength": r"\bcompressive\s+strength\b",
    "setting_time": r"\bsetting\s+time\b",
    "soundness": r"\bsoundness\b",
    "construction_use": r"\b(?:concrete|construction|industrial)\b",
    "impact_protection": r"\bimpact\s+(?:absorption|protection|resistance)\b",
    "penetration_resistance": r"\bpenetration\s+(?:protection|resistance)\b",
    "retention": r"\b(?:retention|chin\s*strap)\b",
    "flow": r"\b(?:flow(?:\s+rate)?|discharge)\b",
    "head": r"\b(?:hydraulic\s+|delivery\s+|total\s+dynamic\s+)?head\b",
    "hydraulic_efficiency": r"\b(?:hydraulic\s+)?efficiency\b",
    "water_application": r"\bwater\b",
    "pvc_insulation": r"\bPVC\b",
    "xlpe_insulation": r"\bXLPE\b",
    "cable_application": r"\b(?:building\s+wiring|supply\s+circuits?|power\s+distribution)\b",
    "underground_installation": r"\bunderground\b",
    "dielectric_testing": r"\bdielectric\s+(?:testing|tests?)\b",
}
