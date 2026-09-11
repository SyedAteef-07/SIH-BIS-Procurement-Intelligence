# Frontend ↔ Backend integration repair

The current `main` branch contains accidental merge concatenations in:
- `frontend/src/InputPage.jsx`
- `frontend/src/ResultsPage.jsx`
- `backend/app/main.py`
- `backend/app/schemas.py`

These files cause duplicate imports/definitions and prevent a clean build/start.

This patch:
- restores one clean FastAPI `/api/analyze` route;
- restores the PostgreSQL + AI-service response contract;
- makes the React input page call the backend only;
- makes the results page consume `recommendations`, `related_standards`, `gaps`, `certifications`, and `warnings`;
- avoids turning raw retrieval/reranker scores into fake percentages;
- adds a real `/api/analyze-pdf` endpoint for text-based PDFs up to 10 MB;
- keeps OCR explicitly out of scope for scanned PDFs.

## Apply

Copy the files from this ZIP over the same paths in your repository.

Then run:

```powershell
git switch main
git pull origin main

cd backend
.venv\Scripts\python -m pip install -r requirements.txt
cd ..

docker compose up -d postgres

cd backend
.venv\Scripts\alembic upgrade head
.venv\Scripts\python -m app.scripts.seed_standards
cd ..
```

Start three terminals:

AI:
```powershell
cd ai
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8001
```

Backend:
```powershell
cd backend
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/bis_procurement"
$env:AI_SERVICE_URL="http://127.0.0.1:8001"
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Frontend:
```powershell
cd frontend
npm ci
npm run dev -- --port 5173
```

Open `http://localhost:5173`.

Text demo:
`11 kV/433 V three phase oil immersed distribution transformer for outdoor installation`
