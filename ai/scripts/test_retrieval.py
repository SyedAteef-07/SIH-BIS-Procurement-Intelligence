"""Run with python -m scripts.test_retrieval; downloads pretrained models on first run."""
from fastapi.testclient import TestClient
from dataclasses import replace
from app.config import Settings
from app.main import create_app
from app.recommendation.recommender import RecommendationEngine, build_engine

CASES = [
    ("Procurement of three phase oil immersed distribution transformers", "IS-DEMO-001"),
    ("Protect workers heads from objects falling on a building site", "IS-DEMO-004"),
    ("Energy efficient fixtures to illuminate roads at night", "IS-DEMO-003"),
    ("equipment for reducing 11kV supply for neighbourhood distribution", "IS-DEMO-001"),
    ("protective headwear against falling construction debris", "IS-DEMO-004"),
    ("plastic pressure pipe for potable municipal water", "IS-DEMO-010"),
    ("oil used for electrical insulation and cooling in transformers", "IS-DEMO-014"),
    ("IP65 dust and water ingress testing of lighting housings", "IS-DEMO-022"),
]


def main():
    settings = replace(Settings(), retrieval_mode="hybrid", min_reranker_score=None)
    print("Loading real models...", flush=True)
    hybrid = build_engine(settings)
    for mode in ["semantic", "hybrid"]:
        engine = hybrid if mode == "hybrid" else RecommendationEngine(
            hybrid.store.documents, hybrid.embedder, hybrid.reranker, replace(settings, retrieval_mode=mode))
        with TestClient(create_app(engine)) as client:
            assert client.get("/health").status_code == 200
            assert client.get("/ready").json()["standards_count"] == len(engine.store.documents)
            for text, expected in CASES:
                response = client.post("/recommend", json={"text": text, "top_k": 5})
                response.raise_for_status()
                results = response.json()["recommendations"]
                first = results[0]["standard"]["id"]
                print(f"{mode}: {text}: {first} (expected {expected})", flush=True)
                assert first == expected, response.json()
            response = client.post("/recommend", json={"text": "ergonomic office chair"})
            response.raise_for_status()
            assert response.json()["has_reliable_match"] is None
            assert all(r["standard"]["is_mock"] for r in response.json()["recommendations"])
    print("All real-model API smoke tests passed.")


if __name__ == "__main__":
    main()
