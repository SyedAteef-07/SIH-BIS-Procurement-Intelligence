"""Optional real PostgreSQL smoke test; point TEST_DATABASE_URL at an isolated DB."""
import os
from pathlib import Path
import httpx
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker
from app.database.models import Standard
from app.database.session import get_db, make_engine
from app.main import app
from app.scripts.seed_standards import seed_standards
from app.services.ai_client import AIClient, get_ai_client
from conftest import ai_payload


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Optional isolated PostgreSQL test")
def test_postgres_migrations_seed_and_api():
    url = os.environ["TEST_DATABASE_URL"]
    assert url.startswith("postgresql"), "This smoke test requires PostgreSQL"
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    command.check(config)
    engine = make_engine(url)
    sessions = sessionmaker(engine)
    try:
        with sessions.begin() as session:
            seed_standards(session)
            seed_standards(session)
            assert session.scalar(select(func.count()).select_from(Standard)) == 40
        def database():
            with sessions() as session:
                yield session
        def upstream(request):
            return httpx.Response(200, json={"status": "ready"} if request.url.path == "/ready"
                                  else ai_payload(("IS-DEMO-008", "IS-DEMO-001")))
        app.dependency_overrides[get_db] = database
        app.dependency_overrides[get_ai_client] = lambda: AIClient(transport=httpx.MockTransport(upstream))
        with TestClient(app) as client:
            response = client.post("/api/analyze", json={"description": "water pump 15 kW", "limit": 2})
            assert response.status_code == 200
            items = response.json()["recommendations"]
            assert [r["number"] for r in items] == ["IS-DEMO-008", "IS-DEMO-001"]
            assert all(r["is_mock"] and r["status"] == "unverified" for r in items)
            assert client.get("/ready").status_code == 200
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
