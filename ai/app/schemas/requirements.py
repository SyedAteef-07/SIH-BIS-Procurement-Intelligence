"""Evidence offsets refer to the original text passed to RequirementExtractor."""
from pydantic import BaseModel, Field


class TechnicalValue(BaseModel):
    raw: str
    value: float | int | None = None
    unit: str | None = None
    kind: str | None = None
    start: int | None = None
    end: int | None = None


class EvidenceItem(BaseModel):
    value: str
    evidence: str
    start: int | None = None
    end: int | None = None
    negated: bool = False


class ExtractedRequirements(BaseModel):
    compressive_strength: list[str] = Field(default_factory=list)
    setting_time: list[str] = Field(default_factory=list)
    soundness: list[str] = Field(default_factory=list)
    construction_use: list[str] = Field(default_factory=list)
    impact_protection: list[str] = Field(default_factory=list)
    penetration_resistance: list[str] = Field(default_factory=list)
    retention: list[str] = Field(default_factory=list)
    flow: list[str] = Field(default_factory=list)
    head: list[str] = Field(default_factory=list)
    hydraulic_efficiency: list[str] = Field(default_factory=list)
    water_application: list[str] = Field(default_factory=list)
    pvc_insulation: list[str] = Field(default_factory=list)
    xlpe_insulation: list[str] = Field(default_factory=list)
    cable_application: list[str] = Field(default_factory=list)
    underground_installation: list[str] = Field(default_factory=list)
    dielectric_testing: list[str] = Field(default_factory=list)

    pressure_ratings: list[str] = Field(default_factory=list)
    joints: list[str] = Field(default_factory=list)
    water_use: list[str] = Field(default_factory=list)
    cleaned_text: str = ""
    product: str | None = None
    product_evidence: str | None = None
    product_type: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    voltages: list[TechnicalValue] = Field(default_factory=list)
    frequencies: list[TechnicalValue] = Field(default_factory=list)
    power_ratings: list[TechnicalValue] = Field(default_factory=list)
    dimensions: list[TechnicalValue] = Field(default_factory=list)
    phase: list[str] = Field(default_factory=list)
    ip_ratings: list[str] = Field(default_factory=list)
    technical_classes: list[str] = Field(default_factory=list)
    installation: list[str] = Field(default_factory=list)
    environment: list[str] = Field(default_factory=list)
    testing_requirements: list[str] = Field(default_factory=list)
    safety_requirements: list[str] = Field(default_factory=list)
    performance_requirements: list[str] = Field(default_factory=list)
    installation_requirements: list[str] = Field(default_factory=list)
    material_requirements: list[str] = Field(default_factory=list)
    certification_requirements: list[str] = Field(default_factory=list)
    evidence: dict[str, list[EvidenceItem]] = Field(default_factory=dict)

    @property
    def technical_attribute_count(self):
        return sum(len(getattr(self, name)) for name in (
            "product_type", "materials", "voltages", "frequencies", "power_ratings",
            "dimensions", "phase", "ip_ratings", "technical_classes", "installation", "environment"))
