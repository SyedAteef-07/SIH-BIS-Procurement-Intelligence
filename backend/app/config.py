"""Environment-backed application configuration."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/bis_intelligence",
    )
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    llm_provider: str = os.getenv("LLM_PROVIDER", "disabled")
    llm_model: str = os.getenv("LLM_MODEL", "")


settings = Settings()
