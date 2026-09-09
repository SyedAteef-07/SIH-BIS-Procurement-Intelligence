"""Run once to populate Neo4j from the current catalog.

Usage:
    py -3.13 -m app.scripts.seed_graph_cli
"""

from ..services import graph_service


def main() -> None:
    if not graph_service.is_available():
        print("Neo4j is not reachable at the configured NEO4J_URI. Check it's running.")
        return
    count = graph_service.seed_graph()
    print(f"Seeded/updated {count} Standard nodes in Neo4j.")


if __name__ == "__main__":
    main()