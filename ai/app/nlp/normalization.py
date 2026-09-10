"""Deterministic normalization; quantities retain their exact source substring."""
import re
import math
from app.nlp import technical_patterns as patterns
from app.schemas.requirements import TechnicalValue

UNITS = {"kv": "kV", "kilovolt": "kV", "kilovolts": "kV", "v": "V", "volt": "V", "volts": "V",
         "hz": "Hz", "hertz": "Hz", "kva": "kVA", "mva": "MVA", "kw": "kW", "mw": "MW",
         "mm": "mm", "cm": "cm", "m": "m"}


def normalize_phase(raw):
    match = patterns.PHASE.fullmatch(raw.strip())
    if not match:
        raise ValueError("Unsupported phase expression")
    return "three_phase" if match.group(1).lower() in {"three", "3"} else "single_phase"


def normalize_technical_value(raw):
    for pattern in (patterns.VOLTAGE, patterns.FREQUENCY, patterns.POWER, patterns.DIMENSION):
        match = pattern.fullmatch(raw)
        if match:
            value = float(match.group("value"))
            if not math.isfinite(value):
                raise ValueError("Technical measurement must be finite")
            return TechnicalValue(raw=raw, value=int(value) if value.is_integer() else value,
                                  unit=UNITS[match.group("unit").casefold()])
    raise ValueError("Unsupported technical measurement")


def normalize_ip_rating(raw):
    match = patterns.IP_RATING.fullmatch(raw.strip())
    if not match:
        raise ValueError("Unsupported IP expression")
    return "IP" + match.group(1)


def normalize_phrase(raw):
    return re.sub(r"[\s-]+", " ", raw).strip().casefold()
