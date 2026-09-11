import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
MULTILINGUAL_EMBEDDING_MODEL = "BAAI/bge-m3"
DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_RETRIEVAL_K = 20
DEFAULT_FINAL_K = 5
DEFAULT_RRF_K = 60


def optional_score():
    value = os.getenv("MIN_RERANKER_SCORE", "").strip()
    return None if value.lower() in {"", "null", "none"} else float(value)


def enrichment_enabled():
    value = os.getenv("QUERY_ENRICHMENT", "false").strip().lower()
    if value not in {"true", "false", "1", "0"}:
        raise ValueError("QUERY_ENRICHMENT must be true, false, 1, or 0")
    return value in {"true", "1"}


@dataclass(frozen=True)
class Settings:
    embedding_mode: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODE", "english"))
    multilingual_enabled: bool = field(default_factory=lambda: os.getenv("MULTILINGUAL_ENABLED", "false").lower() in {"true", "1"})
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL))
    reranker_model: str = field(default_factory=lambda: os.getenv("RERANKER_MODEL", DEFAULT_RERANKER_MODEL))
    dataset_path: Path = field(default_factory=lambda: ROOT / os.getenv("DATASET_PATH", "data/sample_standards.json"))
    retrieval_k: int = field(default_factory=lambda: int(os.getenv("RETRIEVAL_K", str(DEFAULT_RETRIEVAL_K))))
    final_k: int = field(default_factory=lambda: int(os.getenv("FINAL_K", str(DEFAULT_FINAL_K))))
    rrf_k: int = field(default_factory=lambda: int(os.getenv("RRF_K", str(DEFAULT_RRF_K))))
    retrieval_mode: str = field(default_factory=lambda: os.getenv("RETRIEVAL_MODE", "hybrid"))
    min_reranker_score: float | None = field(default_factory=optional_score)
    device: str = field(default_factory=lambda: os.getenv("MODEL_DEVICE", "cpu"))
    query_enrichment: bool = field(default_factory=enrichment_enabled)

    def __post_init__(self):
        if self.embedding_mode not in {"english", "multilingual"}:
            raise ValueError("EMBEDDING_MODE must be english or multilingual")
        if self.embedding_mode == "multilingual":
            object.__setattr__(self, "embedding_model", MULTILINGUAL_EMBEDDING_MODEL)
        if self.retrieval_mode not in {"semantic", "hybrid"}:
            raise ValueError("RETRIEVAL_MODE must be semantic or hybrid")
        if not 1 <= self.final_k <= 50 or self.retrieval_k < self.final_k:
            raise ValueError("Require 1 <= FINAL_K <= 50 and RETRIEVAL_K >= FINAL_K")
        if self.rrf_k < 1:
            raise ValueError("RRF_K must be positive")
        if self.min_reranker_score is not None and not math.isfinite(self.min_reranker_score):
            raise ValueError("MIN_RERANKER_SCORE must be finite or disabled")

    @property
    def index_path(self):
        import hashlib
        directory = {DEFAULT_EMBEDDING_MODEL: "bge-small", MULTILINGUAL_EMBEDDING_MODEL: "bge-m3"}.get(
            self.embedding_model, "custom-" + hashlib.sha256(self.embedding_model.encode()).hexdigest()[:16])
        return ROOT / "indexes" / directory
