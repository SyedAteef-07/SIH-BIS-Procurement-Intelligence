"""python -m app.scripts.seed_standards; imports the shared fictional AI fixture."""
import argparse
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from app.database.models import Standard, StandardKeyword, StandardRelationship, StandardCertification, StandardRequirement
from app.database.repositories.standards import StandardRepository
from app.database.session import SessionLocal, engine

FIXTURE = Path(__file__).resolve().parents[3] / "ai/data/sample_standards.json"
DEMO_NOTE = "Demo metadata only. Verify current BIS/QCO applicability from official BIS sources."
DEMO_RELATIONSHIPS = {
    "001": [("014", "material"), ("015", "test_method"), ("016", "component"), ("025", "safety")],
    "003": [("020", "installation/design"), ("021", "safety"), ("022", "ingress_protection")],
    "005": [("023", "related_product"), ("024", "related_product"), ("025", "safety")],
    "008": [("039", "component"), ("032", "installation_component")],
    "010": [("032", "system_component"), ("034", "system_component"), ("007", "application")],
}
DEMO_CERTIFICATIONS = ("001", "002", "004", "005", "010")


class DemoRequirement(BaseModel):
    key: Literal["product_type", "materials", "voltages", "frequencies", "power_ratings", "dimensions",
                 "phase", "ip_ratings", "technical_classes", "installation", "environment",
                 "testing_requirements", "safety_requirements", "performance_requirements",
                 "installation_requirements", "material_requirements", "certification_requirements",
                 "pressure_ratings", "joints", "water_use"]
    label: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    category: str | None = Field(default=None, max_length=120)
    is_mandatory: bool = True
    source_section: str | None = None


class DemoStandard(BaseModel):
    id: str = Field(pattern=r"^IS-DEMO-[0-9]+$", max_length=120)
    title: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    abstract: str = ""
    keywords: list[str] = Field(default_factory=list)
    revision: str | None = None
    requirements: list[DemoRequirement] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_requirement_keys(self):
        if len({r.key for r in self.requirements}) != len(self.requirements):
            raise ValueError("Requirement keys must be unique within each standard")
        return self


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
        wanted_requirements = {r.key: r for r in row.requirements}
        retained_requirements = {r.requirement_key: r for r in standard.requirements}
        standard.requirements[:] = [r for r in standard.requirements if r.requirement_key in wanted_requirements]
        for key, metadata in wanted_requirements.items():
            requirement = retained_requirements.get(key)
            if requirement is None:
                requirement = StandardRequirement(requirement_key=key)
                standard.requirements.append(requirement)
            requirement.label, requirement.description = metadata.label, metadata.description
            requirement.category, requirement.is_mandatory = metadata.category, metadata.is_mandatory
            requirement.source_section = metadata.source_section
    session.flush()
    standards = StandardRepository(session).get_by_codes([r.id for r in rows])
    existing_links = set(session.execute(select(StandardRelationship.source_standard_id,
        StandardRelationship.target_standard_id, StandardRelationship.relationship_type)).all())
    for source, targets in DEMO_RELATIONSHIPS.items():
        for target, kind in targets:
            source_row, target_row = standards.get("IS-DEMO-" + source), standards.get("IS-DEMO-" + target)
            if source_row is None or target_row is None:
                continue
            key = (source_row.id, target_row.id, kind)
            if key not in existing_links:
                session.add(StandardRelationship(source_standard_id=key[0], target_standard_id=key[1], relationship_type=kind))
                existing_links.add(key)
    for suffix in DEMO_CERTIFICATIONS:
        standard = standards.get("IS-DEMO-" + suffix)
        if standard is None:
            continue
        name = "BIS conformity verification"
        certification = session.scalar(select(StandardCertification).where(
            StandardCertification.standard_id == standard.id, StandardCertification.name == name))
        if certification is None:
            certification = StandardCertification(standard_id=standard.id, name=name)
            session.add(certification)
        certification.authority = "Bureau of Indian Standards"
        certification.applicable, certification.status = None, "unverified"
        certification.note, certification.source_url = DEMO_NOTE, None
    session.flush()
    # Refresh already-loaded collections after idempotent inserts.
    for standard in standards.values():
        session.expire(standard, ["certifications", "outgoing_relationships"])
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
