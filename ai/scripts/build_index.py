"""Build or validate the selected model's isolated FAISS cache."""
from app.config import Settings
from app.nlp.embeddings import EmbeddingModel
from app.retrieval.search import load_standards
from app.retrieval.index_cache import build_or_load_index
import argparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    standards = load_standards(settings.dataset_path)
    embedder = EmbeddingModel(settings.embedding_model, settings.device)
    store = build_or_load_index(standards, embedder, settings, rebuild=args.rebuild)
    print(f"Index {settings.index_path}: {store.index.ntotal} standards, {store.index.d} dimensions")


if __name__ == "__main__":
    main()
