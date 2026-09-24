"""`score`: automatic metrics + LLM judge for one run directory."""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .config import JUDGE_DEFAULTS, deep_merge, resolve
from .dataset import load_dataset
from .embed import get_embedder
from .judge import Judge
from .metrics import exam_metrics
from .rubric import CRITERIA
from .util import read_jsonl, write_json, write_jsonl

JUDGE_EXAM_FIELDS = {  # per-question judge field -> exam-level mean column
    "grounded": "grounding_rate", "blind_correct": "blind_answerability",
    "distractor_valid_rate": "distractor_validity", "distractor_wrong_rate": "distractor_wrong_rate",
    **{f"judge_{c}": f"judge_{c}" for c in CRITERIA},
}


def latest_exams(exams: list[dict]) -> list[dict]:
    """After --resume a (doc, seed) can appear twice; keep the last ok record, else the last one."""
    best: dict[tuple, dict] = {}
    for r in exams:
        k = (r["doc_id"], r["seed"])
        if k not in best or r.get("status") == "ok" or best[k].get("status") != "ok":
            best[k] = r
    return list(best.values())


def score_run(run_dir: str | Path, judge_cfg: dict | None = None, use_judge: bool = True,
              embedder: str = "e5", max_exams: int | None = None, workers: int = 8) -> Path:
    """workers = parallel judge requests (the GenAI server answers in ~10 s per call, so
    sequential scoring of a full arm would take hours)."""
    run_dir = resolve(run_dir)
    meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    exams = latest_exams(read_jsonl(run_dir / "exams.jsonl"))
    if max_exams:
        exams = exams[:max_exams]
    ds = load_dataset(meta["config"]["dataset"])
    gold_by_doc = {d.id: d.gold() for d in ds.documents}
    emb = get_embedder(embedder)
    jcfg = deep_merge(JUDGE_DEFAULTS, judge_cfg or {})
    judge = Judge(jcfg, run_dir / "judge_cache.jsonl") if use_judge else None
    gen_model = meta.get("generator", {}).get("model")
    if judge and gen_model and jcfg["model"].split(":")[0].lower() == str(gen_model).split(":")[0].lower():
        print(f"[score] WARNING: judge model '{jcfg['model']}' is the same family as the generator; "
              f"self-preference bias - pick another judge for the paper.")

    q_rows, e_rows = [], []
    ok = [e for e in exams if e.get("status") == "ok"]
    print(f"[score] {run_dir.name}: {len(ok)}/{len(exams)} usable exams, judge={'on' if judge else 'off'}")
    pool = ThreadPoolExecutor(max_workers=max(1, workers))
    for n, ex in enumerate(exams, 1):
        base = {k: ex.get(k) for k in ("run_id", "arm", "doc_id", "seed", "language", "difficulty", "subject",
                                       "status", "model_used")}
        t = ex.get("timings") or {}
        llm = ex.get("llm") or {}
        erow = {**base, "total_s": t.get("total_s"), "generate_s": t.get("generate_s"),
                "chunk_s": t.get("chunk_s"), "retrieve_s": t.get("retrieve_s"),
                "vram_peak_mib": ex.get("vram_peak_mib"), "llm_calls": llm.get("calls"),
                "prompt_tokens": llm.get("prompt_tokens"), "completion_tokens": llm.get("completion_tokens"),
                "n_chunks": ex.get("n_chunks"),
                "unverified": (ex.get("blueprint") or {}).get("unverified"),
                "replacements": (ex.get("blueprint") or {}).get("replacements"),
                "repairs": (ex.get("blueprint") or {}).get("repairs"),
                "truncated_share": (ex.get("document") or {}).get("truncated_share"),
                "gpu_share": min((m["gpu_share"] for m in ex.get("ollama_ps") or [] if m.get("gpu_share") is not None),
                                 default=None)}
        if ex.get("status") != "ok":
            # fallback = valid JSON but an error message; error = no output at all
            e_rows.append({**erow, "format_compliant": False, "count_ok": False,
                           "valid_json": ex.get("status") == "fallback"})
            continue
        gold = gold_by_doc.get(ex["doc_id"], [])
        em, per_q = exam_metrics(ex, emb, gold)
        erow.update(em)
        judged = []
        for q, qm in zip(ex["questions"], per_q):
            judged.append({**base, "uid": f"{ex['run_id']}|{ex['doc_id']}|{ex['seed']}|{q['qid']}",
                           "qid": q["qid"], "type": q["type"], "text": q["text"], "key": q["key"],
                           "options": q["options"], "citations": q.get("citations"), "bloom": q.get("bloom"),
                           "verified": q.get("verified"),
                           "verifier_on": ((ex.get("blueprint") or {}).get("settings") or {}).get("verifier"),
                           **qm})
        if judge:
            results = list(pool.map(lambda q: judge.judge_question(ex, q), ex["questions"]))
            for row, res in zip(judged, results):
                row.update(res)
        for qf, ef in JUDGE_EXAM_FIELDS.items():
            vals = [r.get(qf) for r in judged if r.get(qf) is not None]
            erow[ef] = float(np.mean([float(v) for v in vals])) if vals else None
        q_rows.extend(judged)
        e_rows.append(erow)
        print(f"  [{n}/{len(exams)}] {ex['doc_id']} seed={ex['seed']} q={len(judged)} "
              f"grounding={_fmt(erow.get('grounding_rate'))} blind={_fmt(erow.get('blind_answerability'))}")

    pool.shutdown()
    write_jsonl(run_dir / "questions.jsonl", q_rows)
    pd.DataFrame(e_rows).to_csv(run_dir / "exam_metrics.csv", index=False)
    write_json(run_dir / "score.json", {"scored": datetime.now().isoformat(timespec="seconds"),
                                        "embedder": emb.name, "judge": judge.describe() if judge else None,
                                        "judge_calls": judge.calls if judge else 0,
                                        "n_exams": len(exams), "n_ok": len(ok), "n_questions": len(q_rows)})
    print(f"[score] wrote questions.jsonl ({len(q_rows)} rows), exam_metrics.csv")
    return run_dir


def _fmt(v) -> str:
    return "-" if v is None else f"{v:.2f}"
