"""Sentence embeddings for duplicate rate, coverage and gold similarity.

Default: intfloat/multilingual-e5-base (same model RuneCarver and Bifrost use).
"bow" is a dependency-free hashed bag-of-words fallback used by the unit tests; do not
report "bow" numbers in the paper.
"""
from __future__ import annotations

import hashlib

import numpy as np

from .util import norm_text

_CACHE: dict[str, "Embedder"] = {}


class Embedder:
    name = "base"

    def encode(self, texts: list[str]) -> np.ndarray:  # rows are L2-normalised
        raise NotImplementedError


class E5Embedder(Embedder):
    def __init__(self, model_name: str = "intfloat/multilingual-e5-base"):
        from sentence_transformers import SentenceTransformer  # heavy import, lazy
        self.name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, texts):
        if not texts:
            return np.zeros((0, 768))
        return np.asarray(self.model.encode([f"query: {t}" for t in texts], normalize_embeddings=True,
                                            batch_size=32, show_progress_bar=False))


class BowEmbedder(Embedder):
    name = "bow"

    def __init__(self, dim: int = 2048):
        self.dim = dim

    def encode(self, texts):
        m = np.zeros((len(texts), self.dim))
        for i, t in enumerate(texts):
            for tok in norm_text(t).split():
                m[i, int(hashlib.md5(tok.encode()).hexdigest(), 16) % self.dim] += 1
        n = np.linalg.norm(m, axis=1, keepdims=True)
        n[n == 0] = 1
        return m / n


def get_embedder(name: str = "e5") -> Embedder:
    if name not in _CACHE:
        _CACHE[name] = BowEmbedder() if name == "bow" else E5Embedder(
            "intfloat/multilingual-e5-base" if name == "e5" else name)
    return _CACHE[name]


def cos_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    return a @ b.T
