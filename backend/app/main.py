"""FastAPI entry point for the BIS procurement intelligence MVP."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .catalog import STANDARDS
from .catalog import BY_NUMBER
from .schemas import AnalyzeRequest, AnalyzeResponse
from .service import recommend

app = FastAPI(
    title="BIS Procurement Intelligence",
    description="Explainable Indian Standards recommendations for procurement specifications.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/standards")
def list_standards(search: str | None = Query(default=None, min_length=1)) -> list[dict]:
    values = STANDARDS
    if search:
        needle = search.casefold()
        values = tuple(
            standard for standard in values
            if needle in f"{standard.number} {standard.title} {standard.scope}".casefold()
        )
    return [
        {
            "number": standard.number,
            "title": standard.title,
            "scope": standard.scope,
            "edition": standard.edition,
            "status": standard.status,
        }
        for standard in values
    ]


@app.get("/api/standards/{standard_number:path}")
def get_standard(standard_number: str) -> dict:
    standard = BY_NUMBER.get(standard_number)
    if standard is None:
        raise HTTPException(status_code=404, detail="standard not found")
    return {
        "number": standard.number,
        "title": standard.title,
        "scope": standard.scope,
        "edition": standard.edition,
        "status": standard.status,
        "keywords": list(standard.keywords),
        "related": list(standard.related),
        "certification": standard.certification,
        "requirements": list(standard.requirements),
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> dict:
    try:
        return recommend(request.description, request.limit)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error