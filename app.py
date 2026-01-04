from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException, Query
from pdf_extract import extract_text_from_pdf


from fastapi import FastAPI

from bm25_index import BM25Index

APP_ROOT = Path(__file__).parent

DEMO_DIR = APP_ROOT / "demo_pdfs"

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


# load all PDFs in demo_pdfs into the in memory index
@app.post("/load_demo")
def load_demo(max_pages: int | None = Query(default=10)) -> dict[str, Any]:
    pdfs = sorted(DEMO_DIR.glob("*.pdf"))
    if not pdfs:
        raise HTTPException(
            status_code=400, detail="No PDFs found in demo_pdfs directory"
        )

    added = 0
    for pdf_path in pdfs:
        try:
            text = extract_text_from_pdf(pdf_path, max_pages=max_pages)
        except Exception:
            continue

        if not text.strip():
            continue

        # stable-ish id for demo docs (simple + readable)
        doc_id = f"demo_{pdf_path.stem}"
        index.add_doc(doc_id=doc_id, filename=pdf_path.name, text=text)
        added += 1

    # build BM25 stats once after loading everything
    index.reindex()
    return {"ok": True, "added": added, **index.stats()}
