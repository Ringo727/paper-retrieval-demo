from __future__ import annotations

import re
from pathlib import Path
import fitz


# pdf_path is the path to the pdf either as a string or as a pathlib.Path
# max_pages caps the number of pages that we are extracting from for quicker processing
def extract_text_from_pdf(pdf_path: str | Path, max_pages: int | None = None) -> str:
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"Pdf not found at the path: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a pdf: {path}")
