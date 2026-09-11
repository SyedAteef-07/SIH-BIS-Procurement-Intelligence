"""python -m app.scripts.seed_standards; imports the shared fictional AI fixture."""
import argparse
import json
from pathlib import Path
from pydantic import BaseModel, Field
from app.database.models import Standard, StandardKeyword
from app.database.repositories.standards import StandardRepository
from app.database.session import SessionLocal, engine

FIXTURE = Path(__file__).resolve().parents[3] / "ai/data/sample_standards.json"


class DemoStandard(BaseModel):
    id: str = Field(pattern=r"^IS-DEMO-[0-9]+$", max_length=120)
    title: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    abstract: str = ""
    keywords: list[str] = Field(default_factory=list)
    revision: str | None = None


def seed_standards(session, path=FIXTURE):
    rows = [DemoStandard.model_validate(row) for row in json.loads(Path(path).read_text(encoding="utf-8-sig"))]
    if not rows or len({r.id for r in rows}) != len(rows):
        raise ValueError("Fixture must contain unique demo identifiers")
    existing = StandardRepository(session).get_by_codes([r.id for r in rows])
    for row in rows:
        standard = existing.get(row.id)
        if standard is None:
            standard = Standard(standard_code=row.id)
            session.add(standard)
        standard.title, standard.scope, standard.abstract = row.title, row.scope, row.abstract
        standard.revision = row.revision
        standard.is_mock, standard.status = True, "unverified"
        wanted = set(row.keywords)
        retained = {k.keyword for k in standard.keywords}
        standard.keywords[:] = [k for k in standard.keywords if k.keyword in wanted]
        standard.keywords.extend(StandardKeyword(keyword=k) for k in sorted(wanted - retained))
    session.flush()
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=FIXTURE)
    args = parser.parse_args()
    if engine is None:
        parser.error("Set DATABASE_URL before seeding")
    with SessionLocal.begin() as session:
        count = seed_standards(session, args.fixture)
    print(f"Seeded {count} fictional standards (idempotent upsert by standard_code).")


if __name__ == "__main__":
    main()
