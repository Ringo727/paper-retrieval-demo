from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional

from rank_bm25 import BM25Okapi

_word_re = re.compile(r"[a-z0-9]+")


# turn text into list of lowercase word tokens (letters and numbers only) for consistent searching
def tokenize(text: str) -> List[str]:
    return _word_re.findall(text.lower())


# make a small preview excerpt around the first place the query match shows up
# if nothing matches, just preview the beginning
def make_snippet(text: str, query_tokens: List[str], window: int = 240) -> str:
    lower = text.lower()

    # earliest match position we find (smaller = earlier in the doc)
    best_pos = None

    # find where any query match token first appears in the text
    for tok in query_tokens:
        pos = lower.find(tok)
        if pos != -1 and (best_pos is None or pos < best_pos):
            best_pos = pos

    # if none of the tokens appear, just return the first window chars
    if best_pos is None:
        return (text[:window] + "…") if len(text) > window else text

    # choose a window centered around the match position
    start = max(0, best_pos - window // 2)
    end = min(len(text), best_pos + window // 2)

    # pull that chunk out and trim extra spaces at the edges
    snippet = text[start:end].strip()

    # add "..." if we cut off text at the front/back
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"

    return snippet


@dataclass
class Doc:
    doc_id: str
    filename: str
    text: str
    tokens: List[str]


class BM25Index:
    def __init__(self) -> None:
        self.docs: List[Doc] = []
        self._bm25: Optional[BM25Okapi] = None

    def add_doc(self, doc_id: str, filename: str, text: str) -> None:
        toks = tokenize(text)
        self.docs.append(Doc(doc_id=doc_id, filename=filename, text=text, tokens=toks))

        # Invalidate index when we add a new doc, so we require reindex() to include new docs
        # cause we're building our corpus for bm25 with all the docs that we have in a current snapshot
        self._bm25 = None

    def reindex(self) -> None:
        corpus = [d.tokens for d in self.docs]
        self._bm25 = BM25Okapi(corpus) if corpus else None
