from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.analyze import router as analyze_router

app = FastAPI(
    title="Portfolio Analyzer API",
    description="Analyse de portefeuille titres à partir de relevés de compte, confrontés aux données de marché.",
    version="0.1.0",
)

allowed_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
