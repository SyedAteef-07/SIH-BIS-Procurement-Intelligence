# BIS Procurement Intelligence

AI-powered procurement intelligence system for government tender specification analysis.

## Problem

Government procurement officers need to identify the correct Indian Standards
for products and services mentioned in procurement tenders. This process can
require manually searching standards, related references, revisions,
amendments, certification requirements, and checking whether tender
specifications contain important missing requirements.

## Solution

Our system uses AI, semantic search, RAG, structured relationships, and
rule-based comparison to assist procurement officers in identifying relevant
BIS standards and detecting potential gaps in tender specifications.

## Core Features

- Tender/Product requirement understanding
- Relevant BIS Standard identification
- Semantic search
- Related and normative standard discovery
- Standard version checking
- Amendment detection
- Certification/compliance information
- Tender requirement vs standard comparison
- Tender gap analysis
- Explainable procurement report

## Architecture

Frontend → Backend API → AI/RAG → Standards Knowledge Base → Database

## Project Status

The frontend dashboard and backend API contract are implemented on the feature
branch. The local catalog is a safe, deterministic seed for development; live
BIS ingestion, embeddings, PostgreSQL, Qdrant, and Neo4j can be introduced
behind the documented service boundary.

## Backend MVP

The FastAPI backend accepts product or tender text and returns ranked standards,
resolved related references, certification guidance, and likely specification
gaps. Start it from the repository root after installing
`backend/requirements.txt`:

```text
uvicorn app.main:app --app-dir backend --reload
```

Use `POST /api/analyze` with `{"description": "PVC electrical cable rated 1100V"}`
or browse the catalog with `GET /api/standards`. The catalog is deliberately
small and deterministic for local development; production deployments can
replace it with the standards database and vector/RAG pipeline without changing
the API response contract.
