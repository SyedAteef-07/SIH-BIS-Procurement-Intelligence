"""FastAPI entry point for the BIS procurement intelligence MVP."""

import re
from typing import Literal
import pymupdf 
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from .database.models import Standard
from .database.repositories.standards import StandardRepository
from .database.session import get_db
from .schemas import AnalysisResponse, AnalyzeRequest, StandardDetail, StandardSummary
from .services.ai_client import AIServiceError, get_ai_client
from .services.response_adapter import adapt_analysis, standard_detail

MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_ANALYSIS_CHARS = 2000

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
def list_standards(
    search: str | None = Query(default=None, min_length=1, max_length=200),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return [standard_detail(s) for s in StandardRepository(db).list_standards(search, limit, offset)]


@app.get("/api/standards/{standard_number:path}", response_model=StandardDetail)
def get_standard(standard_number: str, db: Session = Depends(get_db)) -> dict:
    standard = StandardRepository(db).get_by_code(standard_number)
    if standard is None:
        raise HTTPException(status_code=404, detail="standard not found")
    return standard_detail(standard)


async def _analyze_text(description: str, limit: int, embedding_mode: str, db: Session, ai) -> dict:
    try:
        response = await ai.recommend(description, limit, embedding_mode=embedding_mode)
    except AIServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=str(error)) from error
    return await run_in_threadpool(adapt_analysis, description, response, db)


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    ai=Depends(get_ai_client),
) -> dict:
    return await _analyze_text(request.description, request.limit, request.embedding_mode, db, ai)


@app.post("/api/analyze-pdf", response_model=AnalysisResponse)
async def analyze_pdf(
    file: UploadFile = File(...),
    limit: int = Form(5, ge=1, le=20),
    embedding_mode: Literal["english", "multilingual"] = Form("english"),
    db: Session = Depends(get_db),
    ai=Depends(get_ai_client),
) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are supported")

    payload = await file.read(MAX_PDF_BYTES + 1)
    if len(payload) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF is too large; maximum size is 10 MB")

    try:
        document = pymupdf.open(stream=payload, filetype="pdf")
        text = "\n".join(page.get_text("text") for page in document)
        document.close()
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Could not read this PDF") from exc

    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 3:
        raise HTTPException(
            status_code=422,
            detail="No extractable text was found. Scanned PDFs require OCR, which is not enabled in this demo.",
        )

    was_truncated = len(text) > MAX_ANALYSIS_CHARS
    analysis_text = text[:MAX_ANALYSIS_CHARS]
    result = await _analyze_text(analysis_text, limit, embedding_mode, db, ai)
    if was_truncated:
        result["gap_analysis"]["scope"] = "Only the first 2,000 extracted PDF characters were checked. Missing details may appear elsewhere in the document. A mention does not establish compliance."
        result["warnings"] = list(result.get("warnings", [])) + [
            "PDF text exceeded 2,000 characters; this demo analyzed only the first 2,000 extracted characters."
        ]
    return result


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Metadata database is unavailable or migrations are missing"},
    )


@app.get("/ready")
async def ready(db: Session = Depends(get_db), ai=Depends(get_ai_client)):
    checks = {"database": False, "ai_service": False}
    try:
        await run_in_threadpool(lambda: db.execute(select(Standard.id).limit(1)).first())
        checks["database"] = True
    except SQLAlchemyError:
        pass

    try:
        checks["ai_service"] = await ai.ready()
    except AIServiceError:
        pass

    healthy = all(checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "not_ready", "dependencies": checks},
    )
