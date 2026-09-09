"""Neo4j-backed knowledge graph for Standard nodes and their relationships.

Falls back gracefully to an inert no-op if Neo4j is unreachable, so the
catalog-based MVP flow in service.py never breaks because of this layer.
"""

from __future__ import annotations

import logging

from neo4j import GraphDatabase, basic_auth
from neo4j.exceptions import ServiceUnavailable

from ..catalog import STANDARDS, Standard
from ..config import settings

logger = logging.getLogger(__name__)

_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=basic_auth(settings.neo4j_user, settings.neo4j_password)
        )
    return _driver

def is_available() -> bool:
    try:
        _get_driver().verify_connectivity()
        return True
    except (ServiceUnavailable, Exception):  # noqa: BLE001 - graceful degrade
        return False


def seed_graph() -> int:
    """Create/merge Standard nodes and RELATED_TO edges. Returns node count."""
    driver = _get_driver()
    with driver.session() as session:
        for standard in STANDARDS:
            session.run(
                """
                MERGE (s:Standard {number: $number})
                SET s.title = $title,
                    s.scope = $scope,
                    s.edition = $edition,
                    s.status = $status,
                    s.certification = $certification
                """,
                number=standard.number,
                title=standard.title,
                scope=standard.scope,
                edition=standard.edition,
                status=standard.status,
                certification=standard.certification,
            )
        for standard in STANDARDS:
            for related_number in standard.related:
                session.run(
                    """
                    MATCH (a:Standard {number: $from_number})
                    MERGE (b:Standard {number: $to_number})
                    MERGE (a)-[:RELATED_TO]->(b)
                    """,
                    from_number=standard.number,
                    to_number=related_number,
                )
        result = session.run("MATCH (s:Standard) RETURN count(s) AS n")
        return result.single()["n"]


def related_numbers(standard_number: str) -> list[str]:
    """Graph-traversal related standards (1-hop), supplementing the static list."""
    if not is_available():
        return []
    driver = _get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (s:Standard {number: $number})-[:RELATED_TO]-(other:Standard)
            RETURN DISTINCT other.number AS number
            """,
            number=standard_number,
        )
        return [record["number"] for record in result]


def close() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None