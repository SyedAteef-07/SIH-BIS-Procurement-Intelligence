"""Compiled, unit-bounded patterns; bare procurement numbers are not quantities."""
import re

NUMBER = r"(?<![\w.+-])(?P<value>\d+(?:\.\d+)?)"


def measurement_pattern(units):
    return re.compile(NUMBER + r"\s*(?P<unit>" + units + r")(?!\w)", re.IGNORECASE)


VOLTAGE = measurement_pattern(r"kilovolts?|volts?|kV|V")
FREQUENCY = measurement_pattern(r"hertz|Hz")
POWER = measurement_pattern(r"kVA|MVA|kW|MW")
DIMENSION = measurement_pattern(r"mm|cm|m")
PHASE = re.compile(r"\b(single|three|1|3)[\s\-\u2010-\u2015]+phase\b", re.IGNORECASE)
IP_RATING = re.compile(r"\bIP\s*([0-6][0-9])\b", re.IGNORECASE)
TECHNICAL_CLASS = re.compile(r"\bclass\s+([ABFH])\b", re.IGNORECASE)
INSTALLATION = re.compile(r"\b(indoor|outdoor|underground|overhead)\b", re.IGNORECASE)
ENVIRONMENT = re.compile(r"\b(weatherproof|waterproof)\b", re.IGNORECASE)
MATERIAL = re.compile(r"\b(PVC|XLPE|steel|copper|aluminium|aluminum|cement|concrete)\b", re.IGNORECASE)
PRODUCT_TYPE = re.compile(r"\b(oil[\s-]+immersed|dry[\s-]+type|cast[\s-]+resin|air[\s-]+cooled|centrifugal|LED)\b", re.IGNORECASE)

TEST_TERMS = r"insulation|efficiency|dielectric|hydrostatic|pressure|impact|penetration|temperature\s+rise|winding\s+resistance"
TESTING = re.compile(r"\b(?P<terms>(?:" + TEST_TERMS + r")(?:\s*(?:,|and|&)\s*(?:" + TEST_TERMS + r"))*)\s+(?:testing|tests?)\b", re.IGNORECASE)
TEST_TERM = re.compile(TEST_TERMS, re.IGNORECASE)
SAFETY = re.compile(r"\b(?:electrical\s+safety(?:\s+requirements)?|(?:impact|penetration|shock|fire)\s+(?:resistance|protection)|protection\s+against\s+(?:electric\s+shock|falling\s+objects)|against\s+falling\s+objects)\b", re.IGNORECASE)
PERFORMANCE = re.compile(r"\b(?:(?:minimum\s+)?efficiency(?:\s+of\s+\d+(?:\.\d+)?\s*%)?|(?:minimum\s+)?(?:flow\s+rate|compressive\s+strength|tensile\s+strength)|temperature\s+rise|illumination\s+uniformity)\b", re.IGNORECASE)
INSTALLATION_REQUIREMENT = re.compile(r"\b(?:suitable\s+for\s+|for\s+)?(?:indoor|outdoor|underground|overhead)\s+(?:installation|use)\b", re.IGNORECASE)
MATERIAL_REQUIREMENT = re.compile(r"\b(?:made\s+(?:of|from)|manufactured\s+from|constructed\s+(?:of|from))\s+(?:PVC|XLPE|steel|copper|aluminium|aluminum|cement|concrete)\b", re.IGNORECASE)
CERTIFICATION = re.compile(r"\b(?:BIS\s+certification|ISI\s+marking|ISI\s+mark)(?:\s+(?:is\s+)?required)?\b", re.IGNORECASE)


def is_negated(text, start, end):
    """Conservative local scope, not a full grammatical negation parser."""
    prefix = re.split(r"[.;\n]|\b(?:but|however)\b", text[:start], flags=re.IGNORECASE)[-1]
    # 'not only' is additive rather than negative.
    prefix = re.sub(r"\bnot\s+only\b", "", prefix, flags=re.IGNORECASE)
    # Reset at a new explicit requirement following a comma.
    prefix = re.split(r",\s*(?:must|shall|requires?|with)\b", prefix, flags=re.IGNORECASE)[-1]
    preceding = re.search(r"\b(?:not|no|without|excluding|except)\b(?:\W+\w+){0,6}\W*$", prefix, re.IGNORECASE)
    following = re.match(r"\s+(?:(?:is|are)\s+)?(?:not\s+(?:required|permitted|allowed)|prohibited|excluded)\b", text[end:], re.IGNORECASE)
    return bool(preceding or following)
