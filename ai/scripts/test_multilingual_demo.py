"""Explicit real-model demo, excluded from the normal tests/ suite."""
import json
from app.config import ROOT, Settings
from app.nlp.language import detect_language
from app.recommendation.recommender import build_engine

QUERIES = [
    ("transformer", "11 kV three phase distribution transformer for outdoor use"),
    ("transformer", "बाहरी उपयोग के लिए 11 केवी तीन फेज वितरण ट्रांसफॉर्मर"),
    ("transformer", "ಹೊರಾಂಗಣ ಬಳಕೆಗೆ 11 ಕೆವಿ ಮೂರು ಹಂತದ ವಿತರಣಾ ಟ್ರಾನ್ಸ್‌ಫಾರ್ಮರ್"),
    ("cable", "33 kV XLPE power cable"),
    ("cable", "33 केवी एक्सएलपीई पावर केबल"),
    ("cable", "33 ಕೆವಿ ಎಕ್ಸ್‌ಎಲ್‌ಪಿಇ ಪವರ್ ಕೇಬಲ್"),
]


def main():
    settings = Settings(embedding_mode="multilingual")
    print("Loading BGE-M3 and its separate index...", flush=True)
    engine = build_engine(settings)
    rows = []
    for product, query in QUERIES:
        results = engine.recommend(query)
        row = {"query": query, "detected_language": detect_language(query),
               "reranking_applied": not engine.skip_reranking(query),
               "expected": ["IS-DEMO-001"] if product == "transformer" else ["IS-DEMO-005", "IS-DEMO-024"],
               "results": [{"id": r.standard.id, "title": r.standard.title,
                            "retrieval_score": r.retrieval_score, "retrieval_score_type": r.retrieval_score_type,
                            "reranker_score": r.reranker_score} for r in results]}
        row["expected_first_rank"] = next((i for i, r in enumerate(results, 1) if r.standard.id in row["expected"]), None)
        rows.append(row)
        print(f"{product} {row['detected_language']}: {[r.standard.id for r in results]}", flush=True)
    report = {"model": settings.embedding_model, "index_path": str(settings.index_path),
              "dimension": engine.store.index.d, "standards_count": engine.store.index.ntotal,
              "limitations": "Six authored demo queries, not production calibration; non-English uses dense retrieval without CE or BM25.",
              "queries": rows}
    output = ROOT / "evaluation/results/multilingual_demo.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {output}", flush=True)


if __name__ == "__main__":
    main()
