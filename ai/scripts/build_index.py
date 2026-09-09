"""Build and inspect the in-memory index used by the MVP."""
from app.config import Settings
from app.nlp.embeddings import EmbeddingModel
from app.retrieval.search import load_standards
from app.retrieval.vector_store import VectorStore


def main():
    settings = Settings()
    standards = load_standards(settings.dataset_path)
    embedder = EmbeddingModel(settings.embedding_model, settings.device)
    store = VectorStore()
    store.add(embedder.encode([s.document_text for s in standards]), standards)
    print(f"Built in-memory FAISS index: {store.index.ntotal} standards, {store.index.d} dimensions")


if __name__ == "__main__":
    main()
