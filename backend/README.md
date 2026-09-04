# Backend

The backend exposes a small, deterministic implementation of the production
contract while the standards database and retrieval infrastructure are being
integrated.

## Endpoints

- `GET /health` - liveness probe
- `GET /api/standards?search=cable` - searchable standards catalog
- `GET /api/standards/{number}` - full standard metadata
- `POST /api/analyze` - ranked recommendations, related standards,
  certification guidance, gaps, and an explanation

Example:

```json
{
  "description": "PVC insulated electrical cable suitable for 1100V power distribution",
  "limit": 5
}
```

Run locally from the repository root:

```text
uvicorn app.main:app --app-dir backend --reload
```

The catalog is intentionally replaceable. The service boundary in
`app/service.py` is where vector retrieval, reranking, and graph expansion can
be connected without changing the frontend contract.
