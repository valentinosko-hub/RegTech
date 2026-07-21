from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import cases, home, monitoring, reconciliation, shell
from backend.services.mock_store import store


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.schedule_pending_classification()
    yield


app = FastAPI(title="RegOps Hub API", version="0.1.0", lifespan=lifespan)

# In production, Databricks Apps serves the frontend and backend behind the
# same origin, so this is only needed for local dev flexibility (e.g.
# hitting the API directly on :8000 while iterating).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(home.router)
app.include_router(monitoring.router)
app.include_router(reconciliation.router)
app.include_router(cases.router)
app.include_router(shell.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
