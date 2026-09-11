"""Environment-backed application configuration."""

import os
from dataclasses import dataclass, field
from pathlib import Path
import math
from urllib.parse import urlsplit
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / '.env')
load_dotenv(Path(__file__).resolve().parents[1] / '.env')


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    ai_service_url: str = field(default_factory=lambda: os.getenv("AI_SERVICE_URL", "http://127.0.0.1:8001"))
    ai_timeout_seconds: float = field(default_factory=lambda: float(os.getenv("AI_TIMEOUT_SECONDS", "30")))
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "bisdev123")
    llm_provider: str = os.getenv("LLM_PROVIDER", "disabled")
    llm_model: str = os.getenv("LLM_MODEL", "")

    def __post_init__(self):
        if not math.isfinite(self.ai_timeout_seconds) or self.ai_timeout_seconds <= 0:
            raise ValueError("AI_TIMEOUT_SECONDS must be positive and finite")
        url = urlsplit(self.ai_service_url)
        if url.scheme not in {"http", "https"} or not url.netloc or url.query or url.fragment:
            raise ValueError("AI_SERVICE_URL must be an HTTP(S) base URL")


settings = Settings()
