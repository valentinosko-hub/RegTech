# RegOps Hub

An operational workspace for the RegTech Operations team at eToro — daily
morning briefing, regulatory report monitoring, reconciliation break
review, and case management. Built to run as a Databricks App.

## Status: Phase 1 (mock data)

This is Phase 1 of a 6-phase build (see `.cursorrules`). Everything in the
app is fully interactive, but all data is generated in-memory by the
backend (`backend/services/mock_data.py`, `mock_store.py`) instead of
coming from Lakebase/Delta. The data access layer (`backend/services/
lakebase.py`, `delta.py`, `ai.py`) is already structured the way Phase 2–4
will implement it for real, so routers and the frontend won't need to
change when the mock is swapped for live queries.

## Running locally

**Backend:**

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**Frontend** (in a separate terminal):

```bash
npm install
npm run dev
```

Open http://localhost:3000 — Vite proxies `/api` to the backend on `:8000`.

## Project layout

```
src/            React + TypeScript frontend
  routes/       One file per top-level screen (Home, Monitoring, Reconciliation, Cases)
  components/   UI components, grouped by module + shared/
  hooks/        React Query hooks — the ONLY thing components call for data
  services/     Typed fetch wrappers around the backend API
  types/        Shared TypeScript interfaces (mirror the Lakebase/Delta data model)

backend/        FastAPI backend
  routers/      One router per domain (home, monitoring, reconciliation, cases, shell)
  services/     Data access — lakebase.py, delta.py, ai.py (mocked in Phase 1)
  models/       Pydantic request/response models (camelCase on the wire)

migrations/           Lakebase (Postgres) DDL for Phase 2
infrastructure/       Delta Lake DDL for Phase 3
```

## Architecture rules

See `.cursorrules` for the full non-negotiable constraint list (no ORM, no
agent frameworks, no custom auth, Lakebase/Delta consistency contract,
etc). The short version: this mirrors what will eventually be a real
Databricks App, so keep the mock data behind the same interfaces the real
implementation will use.
