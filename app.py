from __future__ import annotations

import uuid
from fastapi import File, UploadFile
from fastapi.responses import JSONResponse

from pathlib import Path
from typing import Any

from fastapi import HTTPException, Query
from pdf_extract import extract_text_from_pdf

from fastapi import FastAPI

from bm25_index import BM25Index

APP_ROOT = Path(__file__).parent

DEMO_DIR = APP_ROOT / "demo_pdfs"

UPLOAD_DIR = APP_ROOT / "uploads"
UPLOAD_DIR.mkdir(
    exist_ok=True
)  # create uploads directory if it doesn't exist (safety to add to avoid setup issues)


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

        # Make an easy id for the doc using the PDF's filename
        # don't need uuid for this cause QA/QC comes from me knowing that the demo files don't have colliding names
        doc_id = f"demo_{pdf_path.stem}"
        index.add_doc(doc_id=doc_id, filename=pdf_path.name, text=text)
        added += 1

    # build BM25 stats once after loading everything
    index.reindex()
    return {"ok": True, "added": added, **index.stats()}


def _safe_filename(name: str) -> str:
    # Keep only the filename part (prevents weird paths like ../../stuff)
    return Path(name).name


@app.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    max_pages: int | None = Query(default=10),
) -> dict[str, Any]:
    # basic validation
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    filename = _safe_filename(file.filename)
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported")

    # read uploaded bytes
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file upload")

    # short unique id for this upload; this is to guard against double uploads, and other things
    doc_id = uuid.uuid4().hex[:16]

    # store the PDF on disk for the demo session
    out_path = UPLOAD_DIR / f"{doc_id}_{filename}"
    out_path.write_bytes(data)

    # extract text
    try:
        text = extract_text_from_pdf(out_path, max_pages=max_pages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {e}")

    if not text.strip():
        # still store the file, but warn if no text was extracted
        return JSONResponse(
            status_code=200,
            content={
                "doc_id": doc_id,
                "filename": filename,
                "stored_as": out_path.name,
                "warning": "No text extracted (PDF may be scanned or image-based).",
            },
        )

    # add to in memory index; BM25Index will reindex on next search
    index.add_doc(doc_id=doc_id, filename=filename, text=text)

    return {
        "doc_id": doc_id,
        "filename": filename,
        "stored_as": out_path.name,
        "text_chars": len(text),
    }


# rebuild BM25 stats from all docs currently loaded
@app.post("/reindex")
def reindex() -> dict[str, Any]:
    index.reindex()
    return {"ok": True, **index.stats()}


# search both demo + uploads (everything currently in the same index)
# What I mean is there's no separation of corpus for this demo
@app.get("/search")
def search(
    q: str = Query(..., min_length=1),
    k: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    results = index.search(q, best_amount=k)
    return {"query": q, "k": k, "results": results}


# clear the in memory index to reload demo PDFs cleanly again
@app.post("/reset")
def reset() -> dict[str, Any]:
    global index
    index = BM25Index()
    return {"ok": True, "note": "Index cleared."}
