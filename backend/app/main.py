from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, comparison, progress, monitoring

app = FastAPI(
    title="Prism API",
    description="Compare options by surfacing hidden costs and systemic impacts",
    version="0.1.0",
)

# CORS for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
