# System architecture

The current application is deliberately runnable without infrastructure:

`React frontend -> FastAPI -> deterministic catalog and ranking`

The production path is designed as:

`React frontend -> FastAPI -> extraction -> vector retrieval (Qdrant)`
`-> relationship expansion (Neo4j) -> reranking/LLM explanation`
`-> PostgreSQL standards and audit data`

`docker compose up -d` starts PostgreSQL, Qdrant, and Neo4j locally. The
backend configuration in `backend/app/config.py` reads their URLs from the
environment. Integrations should be added behind `backend/app/service.py` so
the API remains stable and the deterministic catalog remains a safe fallback
when a dependency is unavailable.

## Data ownership

- PostgreSQL stores canonical standard metadata and analysis audit records.
- Qdrant stores embeddings for standard titles, scopes, and requirement text.
- Neo4j stores normative, allied, superseded, amendment, and certification
  relationships.
- The frontend only consumes the typed API response; it does not connect to
  infrastructure directly.
