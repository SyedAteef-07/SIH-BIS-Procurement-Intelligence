"""python -m app.scripts.seed_standards; imports the shared fictional AI fixture."""
import argparse
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, model_validator
from app.database.models import Standard, StandardKeyword, StandardRelationship, StandardCertification, StandardRequirement
from app.database.repositories.standards import StandardRepository
from app.database.session import SessionLocal, engine

FIXTURE = Path(__file__).resolve().parents[3] / "ai/data/sample_standards.json"
class DemoRequirement(BaseModel):
    key: Literal["product_type", "materials", "voltages", "frequencies", "power_ratings", "dimensions",
                 "phase", "ip_ratings", "technical_classes", "installation", "environment",
                 "testing_requirements", "safety_requirements", "performance_requirements",
                 "installation_requirements", "material_requirements", "certification_requirements",
                 "pressure_ratings", "joints", "water_use", "compressive_strength", "setting_time", "soundness", "construction_use", "impact_protection", "penetration_resistance", "retention", "flow", "head", "hydraulic_efficiency", "water_application", "pvc_insulation", "xlpe_insulation", "cable_application", "underground_installation", "dielectric_testing"]
    label: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    category: str | None = Field(default=None, max_length=120)
    is_mandatory: bool = True
    source_section: str | None = None


class DemoRelationship(BaseModel):
    standard_code: str = Field(min_length=1, max_length=120)
    relationship_type: str = Field(min_length=1, max_length=80)


class DemoCertification(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    authority: str = Field(min_length=1)
    applicable: bool | None = None
    status: str = "unverified"
    note: str = Field(min_length=1)
    source_url: str | None = None


class DemoStandard(BaseModel):
    id: str = Field(pattern=r"^IS-DEMO-[0-9]+$", max_length=120)
    title: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    abstract: str = ""
    keywords: list[str] = Field(default_factory=list)
    revision: str | None = None
    requirements: list[DemoRequirement] = Field(default_factory=list)
    related_standards: list[DemoRelationship] = Field(default_factory=list)
    certifications: list[DemoCertification] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_requirement_keys(self):
        if len({r.key for r in self.requirements}) != len(self.requirements):
            raise ValueError("Requirement keys must be unique within each standard")
        if len({(r.standard_code, r.relationship_type) for r in self.related_standards}) != len(self.related_standards):
            raise ValueError("Relationships must be unique within each standard")
        if len({c.name for c in self.certifications}) != len(self.certifications):
            raise ValueError("Certification names must be unique within each standard")
        return self


def seed_standards(session, path=FIXTURE):
    rows = [DemoStandard.model_validate(row) for row in json.loads(Path(path).read_text(encoding="utf-8-sig"))]
    if not rows or len({r.id for r in rows}) != len(rows):
        raise ValueError("Fixture must contain unique demo identifiers")
    codes = {r.id for r in rows}
    if any(link.standard_code not in codes for row in rows for link in row.related_standards):
        raise ValueError("Related standard must exist in the fixture")
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
    for row in rows:
        standard = standards[row.id]
        wanted_links = {(standards[r.standard_code].id, r.relationship_type) for r in row.related_standards}
        retained_links = {(r.target_standard_id, r.relationship_type): r for r in standard.outgoing_relationships}
        standard.outgoing_relationships[:] = [r for r in standard.outgoing_relationships
            if (r.target_standard_id, r.relationship_type) in wanted_links]
        for target_id, kind in sorted(wanted_links - retained_links.keys()):
            standard.outgoing_relationships.append(StandardRelationship(target_standard_id=target_id, relationship_type=kind))
        retained_certifications = {c.name: c for c in standard.certifications}
        wanted_names = {c.name for c in row.certifications}
        standard.certifications[:] = [c for c in standard.certifications if c.name in wanted_names]
        for metadata in row.certifications:
            certification = retained_certifications.get(metadata.name)
            if certification is None:
                certification = StandardCertification(name=metadata.name)
                standard.certifications.append(certification)
            certification.authority = metadata.authority
            certification.applicable, certification.status = None, "unverified"
            certification.note, certification.source_url = metadata.note, metadata.source_url
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
