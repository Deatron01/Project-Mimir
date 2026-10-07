"""`view`: one self-contained HTML page for reading the results by eye (Hungarian or English UI).

    python -m mimir_eval view            -> results/viewer.html (all runs under results/)

The page embeds the data (no server, no internet); the layout lives in viewer_template.html. Tabs:

* Summary    - plain-language key findings, ranking with 95% bootstrap CIs, what each pipeline step
               adds, quality vs time, Hungarian vs English, the full table and automatic caveats.
* Methods    - what every arm does, what every metric means and how the statistics are computed.
* Documents  - document x arm matrix; per document the chunking and what retrieval returned.
* Compare    - two arms on their common documents with an exact paired Wilcoxon test.
* Exams      - every exam as a printable test paper or in review mode with the judge's verdicts.

The statistics use the latest run per arm, like `report`. Older runs stay readable in the Exams tab.
"""
from __future__ import annotations

import csv
import json
import math
import re
import statistics
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from .config import resolve
from .schema import stem_is_question
from .scoring import latest_exams
from .util import read_jsonl

SOURCE_CHARS = 2500      # per question, so the page stays small even for long documents
CONTEXT_CHARS = 900      # per retrieved chunk
DOC_CHARS = 20000        # document preview in the Documents tab
NEAR_DUP = 0.85          # difflib ratio on normalised stems -> "near duplicate"
QI_COLS = ["format_compliant", "grounding_rate", "blind_answerability", "distractor_validity"]
METRIC_COLS = QI_COLS + [
    "duplicate_rate", "non_question_rate", "meta_reference_rate", "leakage_rate", "coverage", "recall@3",
    "gold_recall", "judge_correctness", "judge_clarity", "judge_distractor_quality", "judge_bloom_fit",
    "vram_peak_mib", "llm_calls", "total_s", "n_chunks", "replacements", "unverified",
]
# family, English name, English description; Hungarian names come from report.ARM_HU (same as the report)
ARM_INFO = {
    "E0": ("base", "Baseline (naive RAG)", "top-3 retrieved chunks, all 10 questions in one call"),
    "B-doc-L": ("base", "Whole document, local", "the whole document in one prompt, local 7B model"),
    "E1": ("pipeline", "Planning", "plans the concepts first, then writes each question in its own call"),
    "E2": ("pipeline", "Planning + verification", "every question is checked and rewritten if it fails"),
    "E2x": ("pipeline", "Verified by another model", "E2, but a model from another family does the checking"),
    "E2f": ("pipeline", "Verification without blind test", "E2 without the blind answering check"),
    "E2h": ("pipeline", "Verification + hybrid search", "E2 with keyword + semantic retrieval"),
    "E3": ("pipeline", "Verification + concept graph", "E2 plus a concept map of the document"),
    "E4": ("server", "Baseline, server model", "E0 on the university server's large model"),
    "E4b": ("server", "Verification, server model", "E2 on the university server's large model"),
    "B-doc-S": ("server", "Whole document, server", "the whole document in one prompt, server model"),
    "E5a": ("chunk", "Old chunker", "E0 with the RuneCarver version before the chunking fix"),
    "E5b": ("chunk", "Std-based chunking", "E0, cuts where the topic shift exceeds 1.5 standard deviations"),
    "E5c": ("chunk", "Fixed-size chunks", "E0 with plain 800-character chunks"),
}


def arm_info(arm: str) -> dict:
    """Names in both languages; 'E2-gemma4-e4b' (a --model rerun) is named after E2."""
    try:
        from .report import ARM_HU
    except Exception:                                   # matplotlib missing: English names only
        ARM_HU = {}
    base, tag = arm, ""
    if arm not in ARM_INFO:
        for b in sorted(ARM_INFO, key=len, reverse=True):
            if arm.startswith(b + "-"):
                base, tag = b, arm[len(b) + 1:]
                break
    fam, en, den = ARM_INFO.get(base, ("other", arm, ""))
    hu, dhu = dict.get(ARM_HU, base, (en, den)) if ARM_HU else (en, den)
    if tag:
        en, hu = f"{en} ({tag})", f"{hu} ({tag})"
        den, dhu = f"{den}; generator {tag}", f"{dhu}; generátor: {tag}"
    return {"family": fam, "base": base, "tag": tag, "en": en, "hu": hu, "desc_en": den, "desc_hu": dhu}


JUDGE_COLS = ["judge_correctness", "judge_clarity", "judge_distractor_quality", "judge_bloom_fit"]


# ---------------------------------------------------------------- helpers
def _num(v):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if v in ("True", "False"):
        return 1.0 if v == "True" else 0.0
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def _clean(o):
    """NaN/inf -> None so the embedded JSON stays valid."""
    if isinstance(o, float):
        return None if math.isnan(o) or math.isinf(o) else round(o, 5)
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    return o


def _norm(s: str) -> str:
    return re.sub(r"\W+", " ", (s or "").lower()).strip()


def duplicate_of(questions: list[dict]) -> dict[int, int]:
    """index -> index of the earlier question it repeats (exact or near-identical stem)."""
    out, seen = {}, []
    for i, q in enumerate(questions):
        t = _norm(q.get("text", ""))
        for j, s in seen:
            if t and s and (t == s or SequenceMatcher(None, t, s).ratio() > NEAR_DUP):
                out[i] = j
                break
        seen.append((i, t))
    return out


def _chunk_text(c) -> str:
    return c.get("text", "") if isinstance(c, dict) else str(c)


def _chunk_stats(chunks: list) -> dict | None:
    if not chunks:
        return None
    lens = [len(_chunk_text(c)) for c in chunks]
    return {"n": len(lens), "median": statistics.median(lens), "tiny": sum(x < 50 for x in lens),
            "small": sum(x < 200 for x in lens), "max": max(lens)}


def _source(exam: dict, q: dict) -> str:
    chunks = exam.get("chunks") or []
    ids = [i for i in (q.get("context_ids") or []) if isinstance(i, int) and 0 <= i < len(chunks)]
    if ids:
        text = "\n\n".join(_chunk_text(chunks[i]) for i in ids)
    else:
        text = exam.get("context_text") or ""
    return text[:SOURCE_CHARS] + ("…" if len(text) > SOURCE_CHARS else "")


def _metrics(rd: Path) -> dict:
    p = rd / "exam_metrics.csv"
    if not p.exists():
        return {}
    with p.open(encoding="utf-8-sig", newline="") as f:
        return {(r["doc_id"], int(float(r["seed"]))): {k: _num(r.get(k)) for k in METRIC_COLS}
                for r in csv.DictReader(f)}


def quality_index(m: dict | None) -> float | None:
    """Same definition as `report`: mean of the four 0..1 measures that every arm has."""
    return _mean([m.get(c) for c in QI_COLS]) if m else None


# ---------------------------------------------------------------- collect
def collect(results_root: Path) -> tuple[list[dict], dict]:
    runs, docs = [], {}
    latest: dict[str, str] = {}
    for rd in sorted(p for p in results_root.iterdir() if (p / "exams.jsonl").exists()):
        meta = json.loads((rd / "run.json").read_text(encoding="utf-8")) if (rd / "run.json").exists() else {}
        cfg = meta.get("config", {})
        arm = cfg.get("name", rd.name)
        metrics = _metrics(rd)
        if metrics or arm not in latest:
            latest[arm] = rd.name                       # like report.load_latest: last scored run wins
        sfile = rd / "score.json"
        judge = (json.loads(sfile.read_text(encoding="utf-8")).get("judge") or {}).get("model") if sfile.exists() else None
        qfile = rd / "questions.jsonl"
        judged = {q["uid"]: q for q in read_jsonl(qfile)} if qfile.exists() else {}
        gen = cfg.get("generator") or {}
        pipe = cfg.get("pipeline") or {}
        exams = []
        for ex in sorted(latest_exams(read_jsonl(rd / "exams.jsonl")), key=lambda e: (e["doc_id"], e["seed"])):
            doc_text = ex.get("doc_text") or ""
            if ex["doc_id"] not in docs and doc_text:
                docs[ex["doc_id"]] = {"language": ex.get("language"), "subject": ex.get("subject"),
                                      "difficulty": ex.get("difficulty"), "chars": len(doc_text),
                                      "text": doc_text[:DOC_CHARS], "truncated": len(doc_text) > DOC_CHARS}
            raw_q = ex.get("questions") or []
            dups = duplicate_of(raw_q)
            qs = []
            for i, q in enumerate(raw_q):
                j = judged.get(f"{ex['run_id']}|{ex['doc_id']}|{ex['seed']}|{q['qid']}", {})
                qs.append({
                    "qid": q["qid"], "type": q.get("type"), "text": q.get("text", ""),
                    "options": q.get("options") or [], "key": q.get("key"),
                    "bloom": q.get("bloom"), "citations": q.get("citations"), "verified": q.get("verified"),
                    "concept": q.get("planned_concept"), "source": _source(ex, q),
                    "dup_of": dups.get(i), "is_question": stem_is_question(q),
                    **{k: j.get(k) for k in ("grounded", "blind_correct", "meta_reference", "judge_correctness",
                                             "judge_clarity", "judge_distractor_quality", "judge_bloom_fit",
                                             "judge_would_use", "judge_rationale", "key_evidence",
                                             "distractor_valid_rate", "judge_bloom_level", "judge_error",
                                             "key_in_stem")},
                })
            t = ex.get("timings") or {}
            llm = ex.get("llm") or {}
            bp = ex.get("blueprint") or {}
            m = metrics.get((ex["doc_id"], ex["seed"]))
            retrieved = [{"rank": r.get("rank"), "chunk": r.get("chunk_index"), "len": len(_chunk_text(r)),
                          "text": _chunk_text(r)[:CONTEXT_CHARS]} for r in (ex.get("retrieved") or [])[:10]]
            exams.append({
                "doc_id": ex["doc_id"], "seed": ex["seed"], "status": ex.get("status"),
                "language": ex.get("language"), "difficulty": ex.get("difficulty"), "subject": ex.get("subject"),
                "error": ex.get("error") or ex.get("parse_error"), "model": ex.get("model_used"),
                "n_requested": ex.get("n_requested"), "total_s": t.get("total_s"),
                "calls": llm.get("calls"), "calls_by_stage": llm.get("calls_by_stage"), "tokens": llm.get("tokens"),
                "questions": qs, "unverified": bp.get("unverified"), "replacements": bp.get("replacements"),
                "vram": ex.get("vram_peak_mib"), "chunks": _chunk_stats(ex.get("chunks") or []),
                "retrieved": retrieved, "metrics": m,
                "qi": quality_index(m) if ex.get("status") != "error" else None,
                "n_dup": len(dups), "n_nonq": sum(not q["is_question"] for q in qs),
            })
        runs.append({"id": rd.name, "arm": arm, "description": cfg.get("description", ""),
                     "scored": bool(metrics), "exams": exams, "judge": judge,
                     "generator": f"{gen.get('provider', '?')}:{gen.get('model', '?')}",
                     "pipeline": pipe.get("kind"), "seeds_cfg": cfg.get("seeds"),
                     "local": gen.get("provider") not in ("genai",),
                     "chunking": cfg.get("chunking")})
    for r in runs:
        r["latest"] = latest.get(r["arm"]) == r["id"]
    return runs, docs


# ---------------------------------------------------------------- statistics (latest run per arm)
def summarize(runs: list[dict]) -> tuple[list[dict], dict]:
    try:
        from .stats import bootstrap_ci
    except Exception:                                   # scipy missing: no CIs, everything else works
        bootstrap_ci = None
    rows, perdoc = [], {}
    for r in runs:
        if not (r["latest"] and r["scored"]):
            continue
        ok = [e for e in r["exams"] if e["status"] != "error" and e["metrics"]]
        by_doc: dict[str, list[dict]] = {}
        for e in ok:
            by_doc.setdefault(e["doc_id"], []).append(e)
        doc_qi = {d: _mean([e["qi"] for e in es]) for d, es in by_doc.items()}
        perdoc[r["arm"]] = doc_qi
        vals = [v for v in doc_qi.values() if v is not None]
        if bootstrap_ci and vals:
            qi, lo, hi = bootstrap_ci(vals)
        else:
            qi, lo, hi = _mean(vals), None, None

        def doc_mean(col):
            return _mean([_mean([e["metrics"].get(col) for e in es]) for es in by_doc.values()])

        qs = [q for e in ok for q in e["questions"]]
        nq = len(qs)
        row = {
            "arm": r["arm"], "run": r["id"], "description": r["description"], "local": r["local"],
            "generator": r["generator"], "pipeline": r["pipeline"], "judge": r["judge"],
            "qi": qi, "ci_lo": lo, "ci_hi": hi, "n_docs": len(by_doc), "n_exams": len(r["exams"]),
            "n_failed": sum(e["status"] != "ok" for e in r["exams"]),
            "seeds": sorted({e["seed"] for e in r["exams"]}), "docs": sorted({e["doc_id"] for e in r["exams"]}),
            "languages": dict(Counter(e["language"] for e in ok if e["seed"] == min(x["seed"] for x in ok))),
            "time_s": _median([e["total_s"] for e in ok]), "calls": _median([e["calls"] for e in ok]),
            "n_questions": nq,
            "dup_share": sum(q["dup_of"] is not None for q in qs) / nq if nq else None,
            "nonq_share": sum(not q["is_question"] for q in qs) / nq if nq else None,
        }
        for c in METRIC_COLS:
            if c not in ("total_s", "llm_calls"):
                row[c] = doc_mean(c)
        rows.append(row)
    rows.sort(key=lambda x: -(x["qi"] if x["qi"] is not None else -1))
    return rows, perdoc


def build_viewer(results_root: str = "results", out: str | None = None) -> Path:
    root = resolve(results_root)
    runs, docs = collect(root)
    summary, perdoc = summarize(runs)
    out_path = resolve(out) if out else root / "viewer.html"
    payload = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"), "root": str(root),
               "runs": runs, "docs": docs, "summary": summary, "perdoc": perdoc,
               "arms": {a: arm_info(a) for a in sorted({r["arm"] for r in runs})}}
    data = json.dumps(_clean(payload), ensure_ascii=False, allow_nan=False).replace("</", "<\\/")
    out_path.write_text(_template().replace("__DATA__", data), encoding="utf-8")
    n = sum(len(r["exams"]) for r in runs)
    print(f"[view] {len(runs)} runs, {n} exams, {len(summary)} arms in the statistics -> {out_path}")
    return out_path



def _template() -> str:
    return (Path(__file__).with_name("viewer_template.html")).read_text(encoding="utf-8")
