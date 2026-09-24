"""Per-slot retrieval: dense (Bifrost /search) or hybrid (BM25 + dense, reciprocal rank fusion)."""
from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    toks = [t.lower() for t in _TOKEN.findall(text or "")]
    # crude stemming for Hungarian/English: cut long words to a 6-char prefix so that
    # "immunrendszer", "immunrendszert", "immunrendszerben" share a key
    return [t[:6] if len(t) > 6 else t for t in toks if len(t) > 1]


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [tokenize(d) for d in docs]
        self.tf = [Counter(d) for d in self.docs]
        self.avgdl = (sum(len(d) for d in self.docs) / len(self.docs)) if self.docs else 0.0
        df = Counter(t for d in self.docs for t in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        out = []
        for tf, d in zip(self.tf, self.docs):
            s = 0.0
            for t in q:
                if t not in tf:
                    continue
                f = tf[t]
                s += self.idf.get(t, 0.0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / (self.avgdl or 1)))
            out.append(s)
        return out

    def ranking(self, query: str) -> list[int]:
        sc = self.scores(query)
        return [i for i in sorted(range(len(sc)), key=lambda i: -sc[i]) if sc[i] > 0]


def rrf(rankings: list[list[int]], k: int = 60) -> list[int]:
    score: dict[int, float] = {}
    for r in rankings:
        for pos, idx in enumerate(r):
            score[idx] = score.get(idx, 0.0) + 1.0 / (k + pos + 1)
    return sorted(score, key=lambda i: -score[i])
