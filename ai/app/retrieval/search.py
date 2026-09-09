import json
from pathlib import Path
from pydantic import TypeAdapter
from app.schemas.recommendation import Standard


def load_standards(path: Path) -> list[Standard]:
    standards = TypeAdapter(list[Standard]).validate_python(json.loads(path.read_text(encoding="utf-8-sig")))
    if not standards:
        raise ValueError("Standards dataset is empty")
    if len({s.id for s in standards}) != len(standards):
        raise ValueError("Standards dataset contains duplicate IDs")
    for standard in standards:
        if standard.id.startswith("IS-DEMO-"):
            standard.is_mock = True
    return standards
