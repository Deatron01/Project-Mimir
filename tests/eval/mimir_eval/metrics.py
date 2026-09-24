"""Automatic metrics that need no LLM (format, language, diversity, coverage, retrieval)."""
from __future__ import annotations

import numpy as np

from .embed import Embedder, cos_matrix
from .schema import has_meta_reference, question_shape_ok
from .util import evidence_in, token_overlap

DUP_THRESHOLD = 0.90
GOLD_MATCH_THRESHOLD = 0.85
RECALL_KS = (1, 3, 5, 10)


def q_text(q: dict) -> str:
    return f"{q['text']} {q.get('key', '')}".strip()


def question_metrics(q: dict, context: str) -> dict:
    return {
        "shape_ok": question_shape_ok(q),
        "meta_reference": has_meta_reference(q["text"]),
        "key_lexical_support": round(token_overlap(q.get("key", ""), context), 4) if q.get("key") else None,
    }


def duplicate_rate(emb: np.ndarray, threshold: float = DUP_THRESHOLD) -> float | None:
    n = len(emb)
    if n < 2:
        return None
    sim = cos_matrix(emb, emb)
    iu = np.triu_indices(n, k=1)
    return float((sim[iu] > threshold).mean())


def coverage(q_emb: np.ndarray, chunk_emb: np.ndarray) -> tuple[float | None, list[int]]:
    """Share of chunks that are the closest chunk of at least one question."""
    if len(q_emb) == 0 or len(chunk_emb) == 0:
        return None, []
    nearest = cos_matrix(q_emb, chunk_emb).argmax(axis=1).tolist()
    return len(set(nearest)) / len(chunk_emb), nearest


def gold_similarity(q_emb: np.ndarray, gold_emb: np.ndarray) -> dict:
    if len(q_emb) == 0 or len(gold_emb) == 0:
        return {"gold_max_sim_mean": None, "gold_recall": None, "per_question": []}
    sim = cos_matrix(q_emb, gold_emb)
    return {"gold_max_sim_mean": float(sim.max(axis=1).mean()),
            "gold_recall": float((sim.max(axis=0) >= GOLD_MATCH_THRESHOLD).mean()),
            "per_question": sim.max(axis=1).round(4).tolist()}


def retrieval_metrics(probe: list[dict], gold: list[dict], chunks: list[str]) -> dict:
    """recall@k and MRR of the gold evidence, from the run's retrieval probe."""
    by_id = {g["qid"]: g for g in gold}
    recalls = {k: [] for k in RECALL_KS}
    rr = []
    for p in probe:
        g = by_id.get(p["gold_qid"])
        if not g or not g["evidence"]:
            continue
        relevant = {i for i, c in enumerate(chunks) if any(evidence_in(e, c) for e in g["evidence"])}
        if not relevant:
            continue  # evidence not found in any chunk (e.g. extraction changed the text)
        ranks = [r + 1 for r, idx in enumerate(p["retrieved_idx"]) if idx in relevant]
        first = ranks[0] if ranks else None
        for k in RECALL_KS:
            recalls[k].append(1.0 if first is not None and first <= k else 0.0)
        rr.append(1.0 / first if first else 0.0)
    out = {f"recall@{k}": (float(np.mean(v)) if v else None) for k, v in recalls.items()}
    out["mrr"] = float(np.mean(rr)) if rr else None
    out["n_probe"] = len(rr)
    return out


def exam_metrics(exam: dict, embedder: Embedder, gold: list[dict]) -> tuple[dict, list[dict]]:
    """Returns (exam-level metrics, per-question metric dicts in question order)."""
    qs = exam.get("questions", [])
    ctx = exam.get("context_text", "")
    per_q = [question_metrics(q, ctx) for q in qs]
    q_emb = embedder.encode([q_text(q) for q in qs])
    chunks = exam.get("chunks", [])
    chunk_emb = embedder.encode(chunks)
    cov, nearest = coverage(q_emb, chunk_emb)
    gold_emb = embedder.encode([f"{g['text']} {g['key']}" for g in gold]) if gold else np.zeros((0, 1))
    gs = gold_similarity(q_emb, gold_emb) if gold else {"gold_max_sim_mean": None, "gold_recall": None,
                                                         "per_question": []}
    for i, m in enumerate(per_q):
        m["nearest_chunk"] = nearest[i] if nearest else None
        m["gold_max_sim"] = gs["per_question"][i] if gs["per_question"] else None
    fmt = exam.get("format", {})
    ex = {
        "format_compliant": fmt.get("format_compliant", False),
        "count_ok": fmt.get("count_ok", False),
        "n_generated": fmt.get("n_generated", 0),
        "shape_ok_rate": fmt.get("shape_ok_rate", 0.0),
        "valid_json": exam.get("raw_json") is not None,
        "meta_reference_rate": (float(np.mean([m["meta_reference"] for m in per_q])) if per_q else None),
        "duplicate_rate": duplicate_rate(q_emb),
        "coverage": cov,
        "gold_max_sim_mean": gs["gold_max_sim_mean"],
        "gold_recall": gs["gold_recall"],
        **retrieval_metrics(exam.get("probe", []), gold, chunks),
    }
    return ex, per_q
