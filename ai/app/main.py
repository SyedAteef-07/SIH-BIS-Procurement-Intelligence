from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException, Request
from app.config import Settings
from app.recommendation.recommender import build_engine
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
logger = logging.getLogger(__name__)


def create_app(engine=None, settings=None):
    settings = settings or (engine.settings if engine is not None else Settings())

    @asynccontextmanager
    async def lifespan(app):
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
        try:
            app.state.engine = engine if engine is not None else build_engine(settings)
        except Exception as exc:
            logger.error("model_startup_failed error_type=%s", type(exc).__name__)
            raise
        try:
            yield
        finally:
            app.state.engine = None

    app = FastAPI(title="Indian Standards Recommendation AI", lifespan=lifespan)
    app.state.engine = None

    def ready_engine():
        current = app.state.engine
        if current is None or not current.is_ready():
            raise HTTPException(status_code=503, detail="Recommendation engine is not ready")
        return current

    @app.get("/")
    def health():
        ready_engine()
        return {"status": "ready", "service": "standards-recommendation-ai"}

    @app.get("/health")
    def liveness():
        return {"status": "ok"}

    @app.get("/ready")
    def readiness():
        current = ready_engine()
        return {"status": "ready", "standards_count": len(current.store.documents),
                "retrieval_mode": current.settings.retrieval_mode}

    @app.post("/recommend", response_model=RecommendationResponse)
    def recommend(body: RecommendationRequest, request: Request):
        current = ready_engine()
        top_k = body.top_k if "top_k" in body.model_fields_set else settings.final_k
        logger.info("request_received query_length=%d retrieval_mode=%s", len(body.text), current.settings.retrieval_mode)
        try:
            results = current.recommend(body.text, retrieval_k=max(settings.retrieval_k, top_k), final_k=top_k)
        except ValueError as exc:
            logger.warning("request_rejected error_type=%s", type(exc).__name__)
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            logger.error("recommendation_failed error_type=%s", type(exc).__name__)
            raise HTTPException(status_code=500, detail="Recommendation failed") from exc
        response = RecommendationResponse(query=body.text, recommendations=results)
        if not results:
            response.has_reliable_match = False
            response.match_status = "NO_RELIABLE_MATCH"
            response.warning = "No sufficiently reliable standard match was identified."
        elif current.settings.min_reranker_score is not None:
            response.has_reliable_match = True
            response.match_status = "MATCH"
        else:
            response.warning = "Reliability filtering is disabled; returned candidates may be unrelated."
        response.warnings.append(response.warning or "Match passes the configured score cutoff; confidence is not calibrated.")
        if any(s.is_mock for s in current.store.documents):
            response.warnings.insert(0, "Contains fictional IS-DEMO development data. These are not real Indian Standards.")
        return response

    return app


app = create_app()
