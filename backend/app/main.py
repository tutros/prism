import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, comparison, progress, monitoring
from .services.llm import check_backend


@asynccontextmanager
async def lifespan(app: FastAPI):
    check_backend()  # fail fast on a bad LLM_BACKEND or a missing `claude`
    yield


app = FastAPI(
    title="Prism API",
    description="Compare options by surfacing hidden costs and systemic impacts",
    version="0.1.0",
    lifespan=lifespan,
)

_cors_origins_raw = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(health.router)
app.include_router(comparison.router)
app.include_router(progress.router)
app.include_router(monitoring.router)


@app.get("/")
async def root():
    return {"message": "Prism API", "docs": "/docs"}
