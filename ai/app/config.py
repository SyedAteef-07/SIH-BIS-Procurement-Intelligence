import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_RETRIEVAL_K = 20
DEFAULT_FINAL_K = 5
DEFAULT_RRF_K = 60


def optional_score():
    value = os.getenv("MIN_RERANKER_SCORE", "").strip()
    return None if value.lower() in {"", "null", "none"} else float(value)


@dataclass(frozen=True)
class Settings:
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL))
    reranker_model: str = field(default_factory=lambda: os.getenv("RERANKER_MODEL", DEFAULT_RERANKER_MODEL))
    dataset_path: Path = field(default_factory=lambda: ROOT / os.getenv("DATASET_PATH", "data/sample_standards.json"))
    retrieval_k: int = field(default_factory=lambda: int(os.getenv("RETRIEVAL_K", str(DEFAULT_RETRIEVAL_K))))
    final_k: int = field(default_factory=lambda: int(os.getenv("FINAL_K", str(DEFAULT_FINAL_K))))
    rrf_k: int = field(default_factory=lambda: int(os.getenv("RRF_K", str(DEFAULT_RRF_K))))
    retrieval_mode: str = field(default_factory=lambda: os.getenv("RETRIEVAL_MODE", "hybrid"))
    min_reranker_score: float | None = field(default_factory=optional_score)
    device: str = field(default_factory=lambda: os.getenv("MODEL_DEVICE", "cpu"))

    def __post_init__(self):
        if self.retrieval_mode not in {"semantic", "hybrid"}:
            raise ValueError("RETRIEVAL_MODE must be semantic or hybrid")
        if not 1 <= self.final_k <= 50 or self.retrieval_k < self.final_k:
            raise ValueError("Require 1 <= FINAL_K <= 50 and RETRIEVAL_K >= FINAL_K")
        if self.rrf_k < 1:
            raise ValueError("RRF_K must be positive")
        if self.min_reranker_score is not None and not math.isfinite(self.min_reranker_score):
            raise ValueError("MIN_RERANKER_SCORE must be finite or disabled")
