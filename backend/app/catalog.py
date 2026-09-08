"""Small, curated catalog used by the MVP recommendation service.

The production system can replace this repository with PostgreSQL/Qdrant data
without changing the API or ranking contract.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Standard:
    number: str
    title: str
    scope: str
    edition: str
    status: str
    keywords: tuple[str, ...]
    related: tuple[str, ...] = ()
    certification: str | None = None
    requirements: tuple[str, ...] = ()


STANDARDS = (
    Standard(
        "IS 302 (Part 1):2008",
        "Safety of household and similar electrical appliances - General requirements",
        "Electrical appliances rated up to 250 V single phase and 480 V other appliances.",
        "2008",
        "Active",
        ("electrical appliance", "electric appliance", "household appliance", "safety", "विद्युत उपकरण"),
        ("IS 302 (Part 2)", "IS 694"),
        "BIS Product Certification (Scheme-I)",
        ("electric shock protection", "heating and fire safety", "marking and instructions"),
    ),
    Standard(
        "IS 694:2010",
        "PVC insulated unsheathed and sheathed cables for working voltages up to and including 1100 V",
        "PVC insulated cables used in power and lighting installations.",
        "2010",
        "Active with amendments",
        ("cable", "wire", "pvc", "1100v", "electrical cable", "तार", "केबल"),
        ("IS 732", "IS 302 (Part 1)"),
        "BIS Product Certification (Scheme-I)",
        ("conductor resistance", "insulation resistance", "voltage test"),
    ),
    Standard(
        "IS 732:2019",
        "Electrical wiring installations - Code of practice",
        "Design, selection, erection, inspection and testing of low-voltage electrical installations.",
        "2019",
        "Active",
        ("wiring", "installation", "low voltage", "electrical installation", "विद्युत स्थापना"),
        ("IS 694", "IS 3043"),
        None,
        ("earthing", "circuit protection", "inspection and testing"),
    ),
    Standard(
        "IS 15644:2006",
        "Helmets for two-wheeler riders",
        "Protective helmets intended for users of two-wheeled motor vehicles.",
        "2006",
        "Active with amendments",
        ("helmet", "motorcycle", "two wheeler", "protective headgear", "हेलमेट"),
        ("IS 4151",),
        "BIS Product Certification (Scheme-I)",
        ("impact attenuation", "retention system", "field of vision"),
    ),
    Standard(
        "IS 12269:2013",
        "Ordinary Portland cement, 53 grade - Specification",
        "Requirements for 53 grade ordinary Portland cement used in construction.",
        "2013",
        "Active",
        ("cement", "concrete", "construction", "opC", "53 grade", "सीमेंट"),
        ("IS 4031", "IS 650"),
        "BIS Product Certification (Scheme-I)",
        ("compressive strength", "setting time", "soundness"),
    ),
    Standard(
        "IS 3043:2018",
        "Code of practice for earthing",
        "Earthing of electrical installations and systems.",
        "2018",
        "Active",
        ("earthing", "grounding", "electrical installation"),
    ),
    Standard(
        "IS 4031 (Parts 1-15)",
        "Methods of physical tests for hydraulic cement",
        "Physical testing methods used to assess hydraulic cement.",
        "1996-2021",
        "Active",
        ("cement test", "compressive strength", "setting time", "soundness"),
    ),
)

BY_NUMBER = {standard.number: standard for standard in STANDARDS}
