from dataclasses import replace
from types import SimpleNamespace
import json
import faiss
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.config import Settings, DEFAULT_EMBEDDING_MODEL, MULTILINGUAL_EMBEDDING_MODEL
from app.main import create_app
from app.nlp.language import detect_language
from app.retrieval.index_cache import build_or_load_index
from test_quality_api import make_engine


@pytest.mark.parametrize("text,language", [("11 kV three phase transformer", "english"),
    ("बाहरी उपयोग के लिए 11 केवी तीन फेज वितरण ट्रांसफॉर्मर", "hindi"),
    ("ಹೊರಾಂಗಣ ಬಳಕೆಗೆ 11 ಕೆವಿ ಮೂರು ಹಂತದ ವಿತರಣಾ ಟ್ರಾನ್ಸ್‌ಫಾರ್ಮರ್", "kannada"),
    ("XLPE ಪವರ್ ಕೇಬಲ್ 33 kV", "kannada"), ("33 kV पावर केबल", "hindi")])
def test_script_detection(text, language):
    assert detect_language(text) == language


def test_modes_models_and_separate_paths(monkeypatch):
    monkeypatch.delenv("EMBEDDING_MODE", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    english = Settings()
    assert english.embedding_mode == "english" and english.embedding_model == DEFAULT_EMBEDDING_MODEL
    multi = Settings(embedding_mode="multilingual")
    assert multi.embedding_model == MULTILINGUAL_EMBEDDING_MODEL
    assert multi.index_path != english.index_path
    assert multi.index_path.name == "bge-m3" and english.index_path.name == "bge-small"
    monkeypatch.setenv("EMBEDDING_MODEL", "local/custom-model")
    assert Settings().embedding_model == "local/custom-model"
    assert Settings(embedding_mode="multilingual").embedding_model == MULTILINGUAL_EMBEDDING_MODEL
    with pytest.raises(ValueError):
        Settings(embedding_mode="unknown")


def test_bge_m3_has_no_instruction_prefix(monkeypatch):
    from app.nlp import embeddings
    monkeypatch.setattr(embeddings, "SentenceTransformer", lambda *a, **kw: object())
    assert embeddings.EmbeddingModel(MULTILINGUAL_EMBEDDING_MODEL).query_prefix == ""
    assert embeddings.EmbeddingModel(DEFAULT_EMBEDDING_MODEL).query_prefix


def test_index_reload_and_dimension_model_corpus_validation(tmp_path):
    engine = make_engine()
    settings = SimpleNamespace(index_path=tmp_path, embedding_model=MULTILINGUAL_EMBEDDING_MODEL)
    embedder = SimpleNamespace(model=SimpleNamespace(get_sentence_embedding_dimension=lambda: 2),
                              encode=lambda texts: np.eye(2, dtype="float32"))
    standards = engine.store.documents
    built = build_or_load_index(standards, embedder, settings)
    embedder.encode = lambda texts: pytest.fail("Cached vectors should be loaded")
    loaded = build_or_load_index(standards, embedder, settings)
    assert built.search([[1, 0]], 1)[0][0].id == loaded.search([[1, 0]], 1)[0][0].id
    manifest_file = tmp_path / "manifest.json"
    original = manifest_file.read_text()
    for field, value in [("dimension", 384), ("model", DEFAULT_EMBEDDING_MODEL), ("corpus_sha256", "stale")]:
        manifest = json.loads(original)
        manifest[field] = value
        manifest_file.write_text(json.dumps(manifest))
        with pytest.raises(ValueError, match="Incompatible index"):
            build_or_load_index(standards, embedder, settings)
    manifest_file.write_text(original)
    faiss.write_index(faiss.IndexFlatIP(384), str(tmp_path / "index.faiss"))
    with pytest.raises(ValueError, match="Incompatible index"):
        build_or_load_index(standards, embedder, settings)


@pytest.mark.parametrize("query", ["11 केवी वितरण ट्रांसफॉर्मर", "11 ಕೆವಿ ವಿತರಣಾ ಟ್ರಾನ್ಸ್‌ಫಾರ್ಮರ್"])
def test_multilingual_skips_reranker_and_never_applies_english_cutoff(query, monkeypatch):
    english = make_engine()
    multi = make_engine(embedding_mode="multilingual", min_reranker_score=100)
    monkeypatch.setattr(multi.reranker, "score", lambda *args: pytest.fail("English CE must not run"))
    with TestClient(create_app(english, multilingual_engine=multi)) as client:
        response = client.post("/recommend", json={"text": query, "embedding_mode": "multilingual"})
        assert response.status_code == 200
        body = response.json()
        assert body["recommendations"] and all(r["reranker_score"] is None for r in body["recommendations"])
        assert body["reranking_applied"] is False and body["match_status"] == "NOT_ASSESSED"
        assert body["has_reliable_match"] is None
        assert body["recommendations"][0]["retrieval_score_type"] == "cosine"
        assert body["detected_language"] == detect_language(query)


def test_english_backward_compatibility_and_disabled_mode():
    with TestClient(create_app(make_engine())) as client:
        implicit = client.post("/recommend", json={"text": "water pump"}).json()
        explicit = client.post("/recommend", json={"text": "water pump", "embedding_mode": "english"}).json()
        assert implicit == explicit
        assert implicit["reranking_applied"] and implicit["embedding_mode"] == "english"
        assert client.post("/recommend", json={"text": "water pump", "embedding_mode": "unknown"}).status_code == 422
        assert client.post("/recommend", json={"text": "water pump", "embedding_mode": "multilingual"}).status_code == 503


def test_multilingual_english_uses_existing_reranker():
    multi = make_engine(embedding_mode="multilingual")
    with TestClient(create_app(make_engine(), multilingual_engine=multi)) as client:
        body = client.post("/recommend", json={"text": "water pump", "embedding_mode": "multilingual"}).json()
        assert body["reranking_applied"] and body["detected_language"] == "english"
        assert body["recommendations"][0]["reranker_score"] == 7


def test_startup_loads_m3_only_when_enabled(monkeypatch):
    import app.main as main
    loaded = []
    def fake_build(settings):
        loaded.append(settings.embedding_model)
        return make_engine(embedding_mode=settings.embedding_mode)
    monkeypatch.setattr(main, "build_engine", fake_build)
    with TestClient(main.create_app(settings=Settings(multilingual_enabled=False))):
        assert loaded == [DEFAULT_EMBEDDING_MODEL]
    loaded.clear()
    with TestClient(main.create_app(settings=Settings(multilingual_enabled=True))):
        assert loaded == [DEFAULT_EMBEDDING_MODEL, MULTILINGUAL_EMBEDDING_MODEL]
