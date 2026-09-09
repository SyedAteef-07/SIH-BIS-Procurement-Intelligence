import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    reranker_model: str = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    dataset_path: Path = ROOT / os.getenv("DATASET_PATH", "data/sample_standards.json")
    retrieval_k: int = int(os.getenv("RETRIEVAL_K", "20"))
    device: str = os.getenv("MODEL_DEVICE", "cpu")
