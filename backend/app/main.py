from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health, comparison

app = FastAPI(
    title="Hidden Cost Comparator API",
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(comparison.router)


@app.get("/")
async def root():
    return {"message": "Hidden Cost Comparator API", "docs": "/docs"}
