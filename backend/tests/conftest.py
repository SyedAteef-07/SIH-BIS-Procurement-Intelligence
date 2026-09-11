import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database.models import Base
from app.database.session import get_db
from app.main import app
from app.scripts.seed_standards import seed_standards
from app.services.ai_client import AIResponse, get_ai_client


def ai_payload(codes=("IS-DEMO-002",), **overrides):
    return {"recommendations": [{"standard": {"id": code, "title": "AI title must not override DB", "is_mock": True},
             "retrieval_score": 0.031, "reranker_score": 7.91 - i, "retrieval_score_type": "rrf",
             "supporting_evidence": ["Evidence from the retrieval fixture"], "validity": "unverified"}
            for i, code in enumerate(codes)], "match_status": "NOT_ASSESSED", "has_reliable_match": None,
            "warnings": ["Reliability filtering is disabled."], **overrides}


class FakeAI:
    def __init__(self):
        self.payload = ai_payload()
        self.error = None
        self.calls = []

    async def recommend(self, text, top_k, embedding_mode="english"):
        self.calls.append((text, top_k))
        if self.error:
            raise self.error
        return AIResponse.model_validate(self.payload)

    async def ready(self):
        if self.error:
            raise self.error
        return True


@pytest.fixture
def database():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)  # Isolated tests only; production uses Alembic.
    sessions = sessionmaker(engine, expire_on_commit=False)
    with sessions.begin() as session:
        seed_standards(session)
    yield engine, sessions
    engine.dispose()


@pytest.fixture
def api(database):
    _, sessions = database
    fake = FakeAI()
    def override_db():
        with sessions() as session:
            yield session
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_ai_client] = lambda: fake
    try:
        with TestClient(app) as client:
            yield client, fake
    finally:
        app.dependency_overrides.clear()
