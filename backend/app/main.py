"""FastAPI entry point for the BIS procurement intelligence MVP."""

from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from .database.session import get_db
from .database.models import Standard
from .database.repositories.standards import StandardRepository
from .services.ai_client import AIServiceError, get_ai_client
from .services.response_adapter import adapt_analysis, standard_detail
from .schemas import AnalyzeRequest, AnalysisResponse, StandardDetail, StandardSummary

app = FastAPI(
    title="BIS Procurement Intelligence",
    description="Explainable Indian Standards recommendations for procurement specifications.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/standards", response_model=list[StandardSummary])
def list_standards(search: str | None = Query(default=None, min_length=1, max_length=200),
                   limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0),
                   db: Session = Depends(get_db)):
    return [standard_detail(s) for s in StandardRepository(db).list_standards(search, limit, offset)]


@app.get("/api/standards/{standard_number:path}", response_model=StandardDetail)
def get_standard(standard_number: str, db: Session = Depends(get_db)) -> dict:
    standard = StandardRepository(db).get_by_code(standard_number)
    if standard is None:
        raise HTTPException(status_code=404, detail="standard not found")
    return standard_detail(standard)


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalyzeRequest, db: Session = Depends(get_db), ai=Depends(get_ai_client)) -> dict:
    try:
        response = await ai.recommend(request.description, request.limit, embedding_mode=request.embedding_mode)
    except AIServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    return await run_in_threadpool(adapt_analysis, request.description, response, db)


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=503, content={"detail": "Metadata database is unavailable or migrations are missing"})


@app.get("/ready")
async def ready(db: Session = Depends(get_db), ai=Depends(get_ai_client)):
    checks = {"database": False, "ai_service": False}
    try:
        # Probes the migrated table, not only network connectivity.
        await run_in_threadpool(lambda: db.execute(select(Standard.id).limit(1)).first())
        checks["database"] = True
    except SQLAlchemyError:
        pass
    try:
        checks["ai_service"] = await ai.ready()
    except AIServiceError:
        pass
    healthy = all(checks.values())
    return JSONResponse(status_code=200 if healthy else 503,
                        content={"status": "ready" if healthy else "not_ready", "dependencies": checks})
