"""Model-isolated dense indexes with explicit compatibility validation."""
import hashlib
import json
import faiss
from app.retrieval.vector_store import VectorStore


def build_or_load_index(standards, embedder, settings, rebuild=False):
    directory = settings.index_path
    index_file, manifest_file = directory / "index.faiss", directory / "manifest.json"
    dimension = embedder.model.get_sentence_embedding_dimension()
    corpus = json.dumps([s.model_dump() for s in standards], sort_keys=True, ensure_ascii=False)
    expected = {"model": settings.embedding_model, "dimension": dimension,
                "corpus_sha256": hashlib.sha256(corpus.encode()).hexdigest(),
                "standard_ids": [s.id for s in standards]}
    store = VectorStore()
    if not rebuild and (index_file.exists() or manifest_file.exists()):
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            if manifest != expected:
                raise ValueError("model, embedding dimension or corpus differs")
            index = faiss.read_index(str(index_file))
            if not isinstance(index, faiss.IndexFlatIP) or index.d != dimension or index.ntotal != len(standards):
                raise ValueError("FAISS dimension, type or document count differs")
        except Exception as exc:
            raise ValueError(f"Incompatible index at {directory}; rebuild with python -m scripts.build_index --rebuild") from exc
        store.index, store.documents = index, list(standards)
        return store
    store.add(embedder.encode([s.to_retrieval_text() for s in standards]), standards)
    if store.index.d != dimension:
        raise ValueError("Embedding output dimension differs from model declaration")
    directory.mkdir(parents=True, exist_ok=True)
    faiss.write_index(store.index, str(index_file))
    manifest_file.write_text(json.dumps(expected, indent=2), encoding="utf-8")
    return store
