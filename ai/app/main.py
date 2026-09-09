from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from app.config import Settings
from app.recommendation.recommender import build_engine
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse


def create_app(engine=None, settings=None):
    settings = settings or Settings()
    if settings.retrieval_k < 1:
        raise ValueError("RETRIEVAL_K must be positive")

    @asynccontextmanager
    async def lifespan(app):
        app.state.engine = engine if engine is not None else build_engine(settings)
        yield
        app.state.engine = None

    app = FastAPI(title="Indian Standards Recommendation AI", lifespan=lifespan)

    @app.get("/")
    def health():
        return {"status": "ready", "service": "standards-recommendation-ai"}

    @app.post("/recommend", response_model=RecommendationResponse)
    def recommend(body: RecommendationRequest, request: Request):
        try:
            results = request.app.state.engine.recommend(body.text, retrieval_k=max(settings.retrieval_k, body.top_k), final_k=body.top_k)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        response = RecommendationResponse(query=body.text, recommendations=results)
        if any(r.standard.is_mock for r in results):
            response.warnings.insert(0, "Contains fictional IS-DEMO development data. These are not real Indian Standards.")
        return response

    return app


app = create_app()
