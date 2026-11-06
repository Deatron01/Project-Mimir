"""RuneCarver sentence encoder: the windowed encoder matches the old one on short texts and gives
every sentence a real vector on long texts (the old one returned zero vectors after 512 tokens).
Uses a word-level fake tokenizer/model, so no model download is needed."""
import hashlib
import importlib.util
import re
import sys
import types

import numpy as np
import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("sklearn")

from mimir_eval.config import REPO_ROOT  # noqa: E402


def _load_chunker():
    if "transformers" not in sys.modules:
        sys.modules["transformers"] = types.SimpleNamespace(AutoTokenizer=None, AutoModel=None)
    spec = importlib.util.spec_from_file_location("rc_chunker", REPO_ROOT / "services" / "runecarver" / "chunker.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ContextualChunker


class Tok:
    def __call__(self, text, return_tensors=None, truncation=False, max_length=None, return_offsets_mapping=False,
                 add_special_tokens=True):
        spans = [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]
        if not add_special_tokens:
            return {"input_ids": list(range(len(spans)))}
        if truncation and max_length:
            spans = spans[: max_length - 2]
        ids = [0] + [int(hashlib.md5(text[a:b].encode()).hexdigest(), 16) % 997 + 1 for a, b in spans] + [0]
        return {"input_ids": torch.tensor([ids]), "attention_mask": torch.ones(1, len(ids), dtype=torch.long),
                "offset_mapping": torch.tensor([[(0, 0)] + spans + [(0, 0)]])}


class Model:
    config = types.SimpleNamespace(hidden_size=16)

    def __init__(self):
        self.E = torch.randn(1000, 16, generator=torch.Generator().manual_seed(0))

    def __call__(self, input_ids, attention_mask=None):
        return types.SimpleNamespace(last_hidden_state=self.E[input_ids])


@pytest.fixture(scope="module")
def chunker():
    cls = _load_chunker()
    c = cls.__new__(cls)
    c.tokenizer, c.model, c.device = Tok(), Model(), "cpu"
    return c


def _text(n_sent, seed=0):
    rng = np.random.default_rng(seed)
    words = [f"szo{i}" for i in range(300)]
    return " ".join(" ".join(rng.choice(words, rng.integers(5, 15))) + "." for _ in range(n_sent))


def test_short_text_identical(chunker):
    t = _text(20)
    s = chunker._get_sentence_spans(t)
    a, b = chunker._legacy_sentence_embeddings(t, s), chunker._windowed_sentence_embeddings(t, s)
    assert all(np.allclose(x, y) for x, y in zip(a, b))


def test_long_text_no_zero_vectors(chunker):
    t = _text(200)
    s = chunker._get_sentence_spans(t)
    legacy = sum(1 for x in chunker._legacy_sentence_embeddings(t, s) if not np.any(x))
    window = sum(1 for x in chunker._windowed_sentence_embeddings(t, s) if not np.any(x))
    assert legacy > 100 and window == 0
    for enc in ("legacy", "window"):
        chunks, _, _ = chunker.embed_and_chunk(t, encoder=enc, target_chunk_chars=800)
        assert " ".join(chunks).split() == " ".join(x[0] for x in s).split()
