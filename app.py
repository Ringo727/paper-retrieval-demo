from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI

from bm25_index import BM25Index

APP_ROOT = Path(__file__).parent

# initializing router (like router := chi.NewRouter() from Go that I did before)
app = FastAPI()

# using an in memory index for demo
index = BM25Index()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stats")
def stats() -> dict[str, Any]:
    return index.stats()
