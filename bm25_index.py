from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional

from rank_bm25 import BM25Okapi

_word_re = re.compile(r"[a-z0-9]+")


# turn text into list of lowercase word tokens (letters and numbers only) for consistent searching
def tokenize(text: str) -> List[str]:
    return _word_re.findall(text.lower())
