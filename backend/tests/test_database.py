from pathlib import Path
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.models import Standard, StandardKeyword, StandardRelationship
from app.database.repositories.standards import StandardRepository
from app.scripts.seed_standards import seed_standards


def test_seed_twice_and_bulk_query_count(database):
    engine, sessions = database
    with sessions.begin() as session:
        ids = dict(session.execute(select(Standard.standard_code, Standard.id)).all())
        assert seed_standards(session) == 40
        assert seed_standards(session) == 40
        assert dict(session.execute(select(Standard.standard_code, Standard.id)).all()) == ids
        assert session.scalar(select(func.count()).select_from(Standard)) == 40
        assert all(s.is_mock and s.status == "unverified" for s in session.scalars(select(Standard)))
    calls = []
    def count_query(*args):
        calls.append(args[2])
    event.listen(engine, "before_cursor_execute", count_query)
    try:
        with sessions() as session:
            found = StandardRepository(session).get_by_codes(["IS-DEMO-003", "IS-DEMO-001", "unknown", "IS-DEMO-003"])
            assert set(found) == {"IS-DEMO-001", "IS-DEMO-003"}
            assert found["IS-DEMO-001"].keywords
            assert len(calls) == 1
    finally:
        event.remove(engine, "before_cursor_execute", count_query)


def test_repository_lookup_search_and_pagination(database):
    _, sessions = database
    with sessions() as session:
        repo = StandardRepository(session)
        assert repo.get_by_code("missing") is None
        assert repo.get_by_codes([]) == {}
        assert repo.get_by_code("IS-DEMO-001").title == "Distribution Transformers"
        assert len(repo.list_standards(limit=2, offset=2)) == 2
        assert repo.list_standards("helmet")[0].standard_code == "IS-DEMO-004"
        assert repo.list_standards("%") == []


def test_mock_constraint_and_relationship_foreign_keys(database):
    _, sessions = database
    with sessions() as session:
        session.add(Standard(standard_code="IS-DEMO-999", title="Unsafe fixture", is_mock=False))
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()
        session.add(StandardRelationship(source_standard_id=9999, target_standard_id=9998, relationship_type="related"))
        with pytest.raises(IntegrityError):
            session.flush()


def test_alembic_upgrade_seed_and_downgrade(tmp_path):
    url = "sqlite:///" + (tmp_path / "migration.db").as_posix()
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    engine = create_engine(url)
    with Session(engine) as session:
        seed_standards(session)
        seed_standards(session)
        session.commit()
        assert session.scalar(select(func.count()).select_from(Standard)) == 40
        assert session.scalar(select(func.count()).select_from(StandardKeyword)) > 0
    command.check(config)
    engine.dispose()
    command.downgrade(config, "base")
    with engine.connect() as connection:
        assert "standards" not in inspect(connection).get_table_names()
    engine.dispose()
