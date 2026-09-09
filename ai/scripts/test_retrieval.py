"""Run with python -m scripts.test_retrieval; downloads pretrained models on first run."""
from fastapi.testclient import TestClient
from app.main import create_app

CASES = [
    ("Procurement of three phase oil immersed distribution transformers", "IS-DEMO-001"),
    ("Protect workers heads from objects falling on a building site", "IS-DEMO-004"),
    ("Energy efficient fixtures to illuminate roads at night", "IS-DEMO-003"),
]


def main():
    with TestClient(create_app()) as client:
        for text, expected in CASES:
            response = client.post("/recommend", json={"text": text, "top_k": 5})
            response.raise_for_status()
            results = response.json()["recommendations"]
            first = results[0]["standard"]["id"]
            print(f"{text}: {first} (expected {expected})")
            assert first == expected, response.json()
    print("All real-model API smoke tests passed.")


if __name__ == "__main__":
    main()
