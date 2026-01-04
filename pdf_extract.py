from __future__ import annotations

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

    # stores text from each page as a string
    chunks: list[str] = []

    with fitz.open(path) as doc:
        n_pages = doc.page_count
        end = min(n_pages, max_pages) if max_pages is not None else n_pages

        for i in range(end):
            page = doc.load_page(i)
            txt = page.get_text("text")

            # append only if there's actually text to append
            if txt:
                chunks.append(txt)

    raw = "\n".join(chunks)

    # split helps turn \n, \t, or just whitespace into an actual separable list
    cleaned = " ".join(raw.split())

    return cleaned
