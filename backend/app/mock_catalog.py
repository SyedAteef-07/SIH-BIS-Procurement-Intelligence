"""Optional mock/test standards loaded from the ai/data fixture file.

Only used when INCLUDE_MOCK_STANDARDS=true is set — kept out of the
default catalog so demo runs never surface fictional standard numbers.
"""

import json
from pathlib import Path

from .catalog import Standard

_MOCK_JSON_PATH = Path(__file__).resolve().parents[2] / "ai" / "data" / "sample_standards.json"


def load_mock_standards() -> tuple[Standard, ...]:
    if not _MOCK_JSON_PATH.exists():
        return ()
    with _MOCK_JSON_PATH.open(encoding="utf-8-sig") as f:
        raw = json.load(f)
    return tuple(
        Standard(
            number=entry["id"],
            title=entry["title"],
            scope=entry["scope"],
            edition="N/A",
            status="Mock/Test data",
            keywords=tuple(entry.get("keywords", ())),
            is_mock=True,
        )
        for entry in raw
    )