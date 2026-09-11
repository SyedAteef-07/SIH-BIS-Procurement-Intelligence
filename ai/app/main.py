from contextlib import asynccontextmanager
from dataclasses import replace
import logging
from fastapi import FastAPI, HTTPException, Request
from app.config import Settings, DEFAULT_EMBEDDING_MODEL
from app.nlp.language import detect_language
from app.recommendation.recommender import build_engine
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
logger = logging.getLogger(__name__)


def create_app(engine=None, settings=None, multilingual_engine=None):
    settings = settings or (engine.settings if engine is not None else Settings())

    @asynccontextmanager
    async def lifespan(app):
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
        try:
            app.state.engine = engine if engine is not None else build_engine(settings)
            app.state.engines = {settings.embedding_mode: app.state.engine}
            if multilingual_engine is not None:
                app.state.engines["multilingual"] = multilingual_engine
            elif settings.multilingual_enabled and settings.embedding_mode == "english":
                app.state.engines["multilingual"] = build_engine(replace(settings, embedding_mode="multilingual"))
            if settings.embedding_mode == "multilingual":
                app.state.engines["english"] = build_engine(replace(settings, embedding_mode="english", embedding_model=DEFAULT_EMBEDDING_MODEL))
        except Exception as exc:
            logger.error("model_startup_failed error_type=%s", type(exc).__name__)
            raise
        try:
            yield
        finally:
            app.state.engine = None
            app.state.engines = {}

    app = FastAPI(title="Indian Standards Recommendation AI", lifespan=lifespan)
    app.state.engine = None
    app.state.engines = {}

    def ready_engine(mode=None):
        current = app.state.engine if mode is None or mode == settings.embedding_mode else app.state.engines.get(mode)
        if current is None or not current.is_ready():
            raise HTTPException(status_code=503, detail="Requested recommendation mode is not ready. Enable MULTILINGUAL_ENABLED=true at startup for the multilingual demo.")
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
        mode = body.embedding_mode or settings.embedding_mode
        current = ready_engine(mode)
        top_k = body.top_k if "top_k" in body.model_fields_set else current.settings.final_k
        logger.info("request_received query_length=%d retrieval_mode=%s", len(body.text), current.settings.retrieval_mode)
        try:
            results = current.recommend(body.text, retrieval_k=max(current.settings.retrieval_k, top_k), final_k=top_k)
        except ValueError as exc:
            logger.warning("request_rejected error_type=%s", type(exc).__name__)
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            logger.error("recommendation_failed error_type=%s", type(exc).__name__)
            raise HTTPException(status_code=500, detail="Recommendation failed") from exc
        skipped = current.skip_reranking(body.text)
        response = RecommendationResponse(query=body.text, recommendations=results, embedding_mode=mode,
                                          detected_language=detect_language(body.text), reranking_applied=not skipped)
        if not results:
            response.has_reliable_match = False
            response.match_status = "NO_RELIABLE_MATCH"
            response.warning = "No sufficiently reliable standard match was identified."
        elif current.settings.min_reranker_score is not None and not skipped:
            response.has_reliable_match = True
            response.match_status = "MATCH"
        else:
            response.warning = "Reliability filtering is disabled; returned candidates may be unrelated."
        if mode == "multilingual":
            response.warnings.append("Experimental multilingual hackathon demo; not production-calibrated.")
        if skipped:
            response.warning = "English CrossEncoder reranking and its score cutoff were skipped for non-English input; semantic candidates are unassessed."
        response.warnings.append(response.warning or "Match passes the configured score cutoff; confidence is not calibrated.")
        if any(s.is_mock for s in current.store.documents):
            response.warnings.insert(0, "Contains fictional IS-DEMO development data. These are not real Indian Standards.")
        return response

    return app


app = create_app()
