"""`view`: one self-contained HTML page for reading the results by eye.

    python -m mimir_eval view            -> results/viewer.html (all runs under results/)

The page embeds the data (no server, no internet) and has four tabs:

* Overview   - ranking of the arms (quality index with 95% bootstrap CI over documents, the index's
               parts, duplicates, non-question stems, time, LLM calls), quality vs time, a metric heatmap
               and automatic warnings (different document sets, single seed, failed exams).
* Documents  - document x arm matrix of the quality index; per document the chunking and what each
               arm's retrieval returned.
* Compare    - two arms on their common documents: per-document differences and an exact paired
               Wilcoxon test (same statistic as the report).
* Exams      - every exam as a printable test paper (answers hidden until you ask) or in review mode
               with the judge's verdicts, duplicate / non-question flags and the retrieved context.

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
                     "scored": bool(metrics), "exams": exams,
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
            "generator": r["generator"], "pipeline": r["pipeline"],
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
               "runs": runs, "docs": docs, "summary": summary, "perdoc": perdoc}
    data = json.dumps(_clean(payload), ensure_ascii=False, allow_nan=False).replace("</", "<\\/")
    out_path.write_text(TEMPLATE.replace("__DATA__", data), encoding="utf-8")
    n = sum(len(r["exams"]) for r in runs)
    print(f"[view] {len(runs)} runs, {n} exams, {len(summary)} arms in the statistics -> {out_path}")
    return out_path


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mimir results viewer</title>
<style>
:root{--bg:#f7f7f5;--panel:#fff;--ink:#1b1b19;--ink2:#5b5a55;--ink3:#8a8983;--line:#e3e2dc;--accent:#2a78d6;--accent2:#c2610c;
--good:#1f7a3a;--goodbg:#e6f4ea;--bad:#b3261e;--badbg:#fbe9e7;--warn:#8a5a00;--warnbg:#fdf3dc;--key:#e6f4ea;--grid:#ecebe6}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--panel:#1f1f1d;--ink:#f2f1ec;--ink2:#b3b1a8;--ink3:#86847c;--line:#34332f;
--accent:#6aa6f0;--accent2:#f0a35e;--good:#7fd29a;--goodbg:#1d3325;--bad:#f28b82;--badbg:#3a1f1d;--warn:#f0c46a;--warnbg:#3a3018;--key:#1d3325;--grid:#2a2926}}
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;font:14px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--ink);display:flex;flex-direction:column}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.top{display:flex;align-items:center;gap:18px;padding:10px 20px;border-bottom:1px solid var(--line);background:var(--panel);flex-wrap:wrap}
.top h1{font-size:16px;margin:0}.top .gen{margin-left:auto;color:var(--ink3);font-size:12px}
.tabs{display:flex;gap:4px;flex-wrap:wrap}.tabs button{border:1px solid transparent;background:none;color:var(--ink2);padding:6px 12px;border-radius:8px;cursor:pointer;font:inherit}
.tabs button:hover{background:var(--bg)}.tabs button.on{background:var(--bg);border-color:var(--line);color:var(--ink);font-weight:600}
.view{flex:1;overflow:auto;min-height:0}.view[hidden]{display:none}.pad{padding:20px 24px;max-width:1500px}
h2{font-size:17px;margin:22px 0 8px}h2:first-child{margin-top:0}h3{font-size:15px;margin:16px 0 6px}
.note{color:var(--ink2);font-size:13px;margin:0 0 10px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:14px}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-bottom:14px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:9px 12px}
.tile .v{font-size:20px;font-weight:650;font-variant-numeric:tabular-nums}.tile .l{font-size:12px;color:var(--ink2)}
.tile.warn{border-color:var(--warn)}.tile.bad{border-color:var(--bad)}
.warns{list-style:none;padding:0;margin:0}.warns li{padding:7px 10px;border-radius:8px;background:var(--warnbg);color:var(--ink);margin:6px 0;font-size:13px}
.warns li b{color:var(--warn)}
.tw{overflow:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th,td{padding:6px 9px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th{font-weight:600;color:var(--ink2);background:var(--panel);position:sticky;top:0;z-index:1;font-size:12px}
th.s{cursor:pointer}th.s:hover{color:var(--ink)}th.l,td.l{text-align:left}
tr:last-child td{border-bottom:0}tbody tr:hover td{background:var(--bg)}
.chip{font-size:12px;padding:1px 8px;border-radius:999px;border:1px solid var(--line);color:var(--ink2);white-space:nowrap;display:inline-block}
.ok{background:var(--goodbg);color:var(--good);border-color:transparent}.no{background:var(--badbg);color:var(--bad);border-color:transparent}
.mid{background:var(--warnbg);color:var(--warn);border-color:transparent}
.flagv{color:var(--bad);font-weight:600}.muted{color:var(--ink3)}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
svg text{fill:var(--ink2);font-size:11px}svg .lab{fill:var(--ink);font-size:11.5px}
.hm td{text-align:center;min-width:58px}.hm td.l{text-align:left}.hm td.c{cursor:pointer}.hm td.c:hover{outline:2px solid var(--accent);outline-offset:-2px}
.legend{display:flex;gap:14px;font-size:12px;color:var(--ink2);align-items:center;margin:4px 0 8px}
.sw{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:-1px}
#tip{position:fixed;pointer-events:none;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px 9px;font-size:12px;
box-shadow:0 4px 16px rgba(0,0,0,.15);max-width:360px;z-index:50;display:none;white-space:pre-line}
select,input[type=search]{padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);font:inherit}
button.btn{padding:5px 12px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink);cursor:pointer;font:inherit}
button.btn:hover{border-color:var(--accent)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{border:0;background:var(--panel);color:var(--ink2);padding:5px 12px;cursor:pointer;font:inherit}.seg button.on{background:var(--accent);color:#fff}
.app{display:grid;grid-template-columns:300px 1fr;height:100%}
aside{border-right:1px solid var(--line);background:var(--panel);overflow:auto;padding:14px}
aside label{display:block;font-size:12px;color:var(--ink2);margin:12px 0 4px}aside select,aside input[type=search]{width:100%}
.exmain{overflow:auto;padding:20px 28px}
.exam{display:block;width:100%;text-align:left;padding:7px 9px;margin:3px 0;border:1px solid transparent;border-radius:8px;background:none;color:var(--ink);cursor:pointer;font:inherit;font-size:13px}
.exam:hover{background:var(--bg)}.exam.on{border-color:var(--accent);background:var(--bg)}.exam small{color:var(--ink2);display:block}
.head h2{margin:0 0 6px;font-size:18px}.stat{font-size:13px;color:var(--ink2)}
.toggle{display:flex;gap:6px;align-items:center;font-size:13px;margin-top:12px}.toggle label{margin:0}
.q{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:12px}
.q.flag{border-left:4px solid var(--bad)}.qt{font-weight:600;margin:6px 0 8px}
.q ol{margin:0 0 8px;padding-left:22px}.q li{padding:3px 6px;border-radius:6px;margin:2px 0}.q li.key{background:var(--key);font-weight:600}
details{margin-top:8px}summary{cursor:pointer;color:var(--ink2);font-size:13px}
.src{white-space:pre-wrap;font-size:13px;background:var(--bg);border-radius:8px;padding:10px;margin-top:6px;max-height:320px;overflow:auto}
.why{font-size:13px;color:var(--ink2);margin-top:6px}.empty{color:var(--ink2);padding:40px 0}
.ctx{border:1px solid var(--line);border-radius:8px;padding:8px 10px;margin:6px 0;font-size:13px;white-space:pre-wrap;background:var(--bg)}
.ctx.tiny{border-color:var(--bad);background:var(--badbg)}
.paper{background:#fff;color:#111;border:1px solid var(--line);border-radius:6px;max-width:820px;margin:0 auto;padding:42px 54px;
font-family:Georgia,"Times New Roman",serif;font-size:15.5px;line-height:1.55;box-shadow:0 2px 12px rgba(0,0,0,.06)}
.paper .pt{font-size:22px;font-weight:700;text-align:center;margin:0 0 4px}.paper .pm{text-align:center;color:#555;font-size:13px;margin-bottom:18px;font-family:system-ui,sans-serif}
.paper .pn{display:flex;justify-content:space-between;gap:12px;border-top:1.5px solid #111;border-bottom:1px solid #999;padding:10px 0;margin-bottom:12px;font-size:14px;flex-wrap:wrap}
.paper .pi{font-style:italic;margin:0 0 18px}
.paper ol.pq{padding-left:26px;margin:0}.paper ol.pq>li{margin:0 0 20px;page-break-inside:avoid;break-inside:avoid}
.paper .ps{font-weight:600;margin-bottom:6px}.paper .po{display:grid;gap:3px;padding-left:4px}
.paper .opt{display:flex;gap:10px;align-items:baseline;padding:2px 6px;border-radius:4px}
.paper .bub{display:inline-flex;width:22px;height:22px;border:1.3px solid #333;border-radius:50%;align-items:center;justify-content:center;font-size:12px;flex:none;font-family:system-ui,sans-serif}
.paper .opt.right{background:#e3f3e7}.paper .opt.right .bub{background:#1f7a3a;border-color:#1f7a3a;color:#fff}
.paper .lines{border-bottom:1px solid #999;height:26px;margin:4px 0}
.paper .akey{margin-top:26px;border-top:1.5px solid #111;padding-top:10px;font-family:system-ui,sans-serif;font-size:13px}
.paper .akey span{display:inline-block;margin:2px 14px 2px 0}
.paper .pflag{font-family:system-ui,sans-serif;font-size:11px;color:#b3261e;margin-left:6px;font-weight:400}
@media (max-width:900px){.grid2{grid-template-columns:1fr}.app{grid-template-columns:1fr;height:auto}aside{border-right:0;border-bottom:1px solid var(--line)}.paper{padding:24px 18px}}
@media print{.top,aside,.noprint{display:none!important}body{display:block;background:#fff}.view{overflow:visible}.app{display:block;height:auto}
.exmain{overflow:visible;padding:0}.paper{border:0;box-shadow:none;max-width:none;padding:0}.paper .pflag{display:none}}
</style>
</head>
<body>
<div class="top noprint">
  <h1>Mimir results viewer</h1>
  <nav class="tabs" id="tabs">
    <button data-t="overview">Overview</button><button data-t="documents">Documents</button>
    <button data-t="compare">Compare arms</button><button data-t="exams">Exams</button>
  </nav>
  <div class="gen" id="gen"></div>
</div>
<section class="view" id="v-overview"><div class="pad" id="overview"></div></section>
<section class="view" id="v-documents" hidden><div class="pad" id="documents"></div></section>
<section class="view" id="v-compare" hidden><div class="pad" id="compare"></div></section>
<section class="view" id="v-exams" hidden>
<div class="app">
<aside>
  <label for="run">Run (arm)</label><select id="run"></select>
  <div class="stat" id="rundesc"></div>
  <label for="find">Search questions</label><input id="find" type="search" placeholder="word in a question or answer">
  <div class="toggle"><input type="checkbox" id="problems"><label for="problems">Only problems</label></div>
  <label>Exams <span class="muted">(← → to step)</span></label><div id="exams"></div>
</aside>
<div class="exmain" id="main"><div class="empty">Pick a run and an exam on the left.</div></div>
</div>
</section>
<div id="tip"></div>
<script id="data" type="application/json">__DATA__</script>
<script>
"use strict";
const D = JSON.parse(document.getElementById('data').textContent);
const RUNS = D.runs, SUM = D.summary, DOCS = D.docs, PERDOC = D.perdoc;
const ARMS = SUM.map(r => r.arm);
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct = v => v == null ? '–' : Math.round(v * 100) + '%';
const f2 = v => v == null ? '–' : v.toFixed(2);
const dur = s => s == null ? '–' : s < 90 ? Math.round(s) + ' s' : (s / 60).toFixed(1) + ' min';
const LETTERS = 'ABCDEFGHIJ';
const latestRun = arm => RUNS.find(r => r.arm === arm && r.latest);
const sumOf = arm => SUM.find(r => r.arm === arm);
function chip(label, state = '', tip = '') { return `<span class="chip ${state}"${tip ? ` data-tip="${esc(tip)}"` : ''}>${esc(label)}</span>`; }
function yesno(v, yes, no) { return v == null ? '' : chip(v ? yes : no, v ? 'ok' : 'no'); }
function shade(g) { g = Math.max(0, Math.min(1, g)); return `color-mix(in srgb, var(--accent) ${Math.round(6 + g * 50)}%, var(--panel))`; }
$('#gen').textContent = `generated ${D.generated} · ${RUNS.length} runs`;

/* ---------------- tooltip ---------------- */
const tip = $('#tip');
document.addEventListener('mousemove', ev => {
  const t = ev.target.closest && ev.target.closest('[data-tip]');
  if (!t) { tip.style.display = 'none'; return; }
  tip.textContent = t.getAttribute('data-tip'); tip.style.display = 'block';
  const w = tip.offsetWidth, h = tip.offsetHeight;
  tip.style.left = Math.max(4, Math.min(ev.clientX + 14, innerWidth - w - 8)) + 'px';
  tip.style.top = (ev.clientY + 16 + h > innerHeight ? ev.clientY - h - 10 : ev.clientY + 16) + 'px';
});

/* ---------------- routing ---------------- */
let tab = 'overview';
function show(t, push = true) {
  tab = t;
  document.querySelectorAll('#tabs button').forEach(b => b.classList.toggle('on', b.dataset.t === t));
  ['overview', 'documents', 'compare', 'exams'].forEach(x => $('#v-' + x).hidden = x !== t);
  if (t === 'overview') renderOverview();
  if (t === 'documents') renderDocuments();
  if (t === 'compare') renderCompare();
  if (t === 'exams') { renderExams(); renderMain(); }
  if (push) setHash();
}
function setHash() {
  let h = tab;
  if (tab === 'documents' && docSel) h += '/' + encodeURIComponent(docSel);
  if (tab === 'compare') h += '/' + encodeURIComponent(cmpA) + '/' + encodeURIComponent(cmpB);
  if (tab === 'exams' && run) h += '/' + encodeURIComponent(run.id) + (exam ? '/' + encodeURIComponent(exam.doc_id) + '/' + exam.seed : '');
  history.replaceState(null, '', '#' + h);
}
document.querySelectorAll('#tabs button').forEach(b => b.onclick = () => show(b.dataset.t));
function openExam(runId, doc, seed) {
  run = RUNS.find(r => r.id === runId) || run;
  exam = run ? (run.exams.find(e => (doc == null || e.doc_id === doc) && (seed == null || e.seed == seed)) || null) : null;
  show('exams');
}
function bindLinks(root) {
  root.querySelectorAll('[data-open]').forEach(a => a.onclick = ev => { ev.preventDefault(); openExam(a.dataset.open, null, null); });
  root.querySelectorAll('[data-exam]').forEach(a => a.onclick = ev => { ev.preventDefault(); const [r, d, s] = a.dataset.exam.split('|'); openExam(r, d, s === '' ? null : +s); });
  root.querySelectorAll('a[href="#compare"],a[href="#documents"]').forEach(a => a.onclick = ev => { ev.preventDefault(); show(a.getAttribute('href').slice(1)); });
}

/* ================= OVERVIEW ================= */
const COLS = [
  {k: 'rank', h: '#', fmt: (r, i) => i + 1, nosort: true},
  {k: 'arm', h: 'Arm', l: true, fmt: r => `<a href="#" data-open="${esc(r.run)}" data-tip="${esc(r.description + '\n' + r.generator + ' · ' + r.run)}"><b>${esc(r.arm)}</b></a> ${r.local ? chip('local') : chip('server', 'mid')}`},
  {k: 'qi', h: 'Quality index · 95% CI', fmt: r => dotCI(r), tip: 'Mean of format, grounded, blind-solvable and good distractors; per document, then over documents. CI: bootstrap over documents.'},
  {k: 'format_compliant', h: 'Format', p: 1},
  {k: 'grounding_rate', h: 'Grounded', p: 1, tip: 'Judge: the key is supported by the source text'},
  {k: 'blind_answerability', h: 'Blind-solvable', p: 1, tip: 'The judge answers without seeing the key and picks the keyed option'},
  {k: 'distractor_validity', h: 'Good distractors', p: 1},
  {k: 'dup_share', h: 'Duplicates', p: 1, bad: .15, tip: 'Share of questions that repeat an earlier question of the same exam (exact or near-identical stem). Not part of the index.'},
  {k: 'nonq_share', h: 'Not a question', p: 1, bad: .15, tip: 'MCQ stems that do not end in "?" or ":" (statements, "Describe…"). Not part of the index.'},
  {k: 'meta_reference_rate', h: '"The text says"', p: 1, bad: .1, tip: 'Stems that refer to "the text / the passage"'},
  {k: 'coverage', h: 'Coverage', p: 1, tip: 'Share of document chunks that are the nearest chunk of at least one question'},
  {k: 'judge_correctness', h: 'Correct /5', d: 2},
  {k: 'judge_distractor_quality', h: 'Distr. /5', d: 2},
  {k: 'time_s', h: 'Time / exam', fmt: r => dur(r.time_s), tip: 'Median wall time for one exam'},
  {k: 'calls', h: 'LLM calls', d: 0},
  {k: 'n_docs', h: 'Docs · exams · seeds', fmt: r => `${r.n_docs} · ${r.n_exams}${r.n_failed ? ` <span class="flagv" data-tip="failed exams">(${r.n_failed}✗)</span>` : ''} · ${r.seeds.length}`},
];
const LOWER_BETTER = new Set(['arm', 'time_s', 'calls', 'dup_share', 'nonq_share', 'meta_reference_rate']);
let sortK = 'qi', sortDir = -1, ciLo = 0;
function dotCI(r) {
  const W = 150, x = v => 5 + (v - ciLo) / (1 - ciLo) * (W - 10);
  if (r.qi == null) return '–';
  const w = r.ci_lo != null ? `<line x1="${x(r.ci_lo)}" x2="${x(r.ci_hi)}" y1="8" y2="8" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round" opacity=".45"/>` : '';
  return `<span data-tip="${esc(`${r.arm}: ${f2(r.qi)} (95% CI ${f2(r.ci_lo)}–${f2(r.ci_hi)}), ${r.n_docs} documents`)}"><svg width="${W}" height="16" style="vertical-align:middle">
    <line x1="5" x2="${W - 5}" y1="8" y2="8" stroke="var(--grid)"/>${w}<circle cx="${x(r.qi)}" cy="8" r="4.5" fill="var(--accent)" stroke="var(--panel)" stroke-width="2"/></svg>
    <b style="display:inline-block;width:34px;text-align:right">${f2(r.qi)}</b></span>`;
}
function cell(c, r, i) {
  if (c.fmt) return c.fmt(r, i);
  const v = r[c.k];
  const s = c.p ? pct(v) : v == null ? '–' : v.toFixed(c.d ?? 2);
  return c.bad != null && v != null && v > c.bad ? `<span class="flagv">${s}</span>` : s;
}
function warnings() {
  const out = [];
  if (!SUM.length) return out;
  const sig = r => r.docs.join('|'), cnt = {};
  SUM.forEach(r => cnt[sig(r)] = (cnt[sig(r)] || 0) + 1);
  const main = Object.entries(cnt).sort((a, b) => b[1] - a[1])[0][0];
  const odd = SUM.filter(r => sig(r) !== main);
  if (odd.length) out.push(`<b>Different document sets.</b> ${odd.map(r => `${esc(r.arm)} (${r.docs.length} docs: ${esc(r.docs.slice(0, 3).join(', '))}${r.docs.length > 3 ? '…' : ''})`).join('; ')} did not run on the same ${main.split('|').length} documents as the other arms, so their rank is not comparable. <a href="#compare">Compare arms</a> uses only common documents.`);
  const maxSeeds = Math.max(...SUM.map(r => r.seeds.length));
  const few = SUM.filter(r => r.seeds.length < maxSeeds);
  if (few.length) out.push(`<b>Fewer seeds.</b> ${few.map(r => esc(r.arm)).join(', ')} ran with ${few[0].seeds.length} seed(s), the others with ${maxSeeds}.`);
  const failed = SUM.filter(r => r.n_failed);
  if (failed.length) out.push(`<b>Failed exams.</b> ` + failed.map(r => latestRun(r.arm).exams.filter(e => e.status !== 'ok')
    .map(e => `<a href="#" data-exam="${esc(r.run)}|${esc(e.doc_id)}|${e.seed}">${esc(r.arm)} · ${esc(e.doc_id)} · seed ${e.seed}</a> (${esc((e.error || e.status || '').slice(0, 80))})`).join(', ')).join('; ') + '. Left out of the statistics.');
  const nd = Math.max(...SUM.map(r => r.n_docs));
  if (nd < 10) out.push(`<b>Too few documents for significance.</b> With ${nd} documents the smallest possible two-sided exact Wilcoxon p is ${(2 / 2 ** nd).toFixed(3)}; after a Holm correction over several comparisons nothing can reach p < 0.05. Evaluate at least 10 documents per arm.`);
  const dup = SUM.filter(r => r.dup_share > .15), nq = SUM.filter(r => r.nonq_share > .15);
  if (dup.length || nq.length) out.push(`<b>Not in the quality index.</b> ${dup.length ? `Many repeated questions: ${dup.map(r => `${esc(r.arm)} ${pct(r.dup_share)}`).join(', ')}. ` : ''}${nq.length ? `Many stems that are not questions: ${nq.map(r => `${esc(r.arm)} ${pct(r.nonq_share)}`).join(', ')}.` : ''}`);
  const tiny = [];
  RUNS.filter(r => r.latest).forEach(r => {
    const seen = new Set();
    r.exams.forEach(e => {
      if (seen.has(e.doc_id) || !e.retrieved.length) return; seen.add(e.doc_id);
      const top = e.retrieved.slice(0, 3);
      if (top.every(c => c.len < 50)) tiny.push(`${r.arm}/${e.doc_id}`);
    });
  });
  if (tiny.length) out.push(`<b>Retrieval returned only tiny chunks</b> (every top-3 chunk under 50 characters) for ${tiny.length} arm/document pairs: ${esc(tiny.slice(0, 8).join(', '))}${tiny.length > 8 ? '…' : ''}. See <a href="#documents">Documents</a>.`);
  return out;
}
function renderOverview() {
  if (!SUM.length) { $('#overview').innerHTML = '<div class="empty">No scored runs yet (run <code>score</code> first). The Exams tab still works.</div>'; return; }
  const exams = RUNS.filter(r => r.latest && r.scored).flatMap(r => r.exams);
  const nq = exams.reduce((s, e) => s + e.questions.length, 0);
  const docs = new Set(exams.map(e => e.doc_id));
  const fails = exams.filter(e => e.status !== 'ok').length;
  ciLo = Math.max(0, Math.floor(Math.min(...SUM.map(r => r.ci_lo ?? r.qi ?? 1)) * 10) / 10);
  const rows = [...SUM].sort((a, b) => {
    const va = a[sortK], vb = b[sortK];
    if (typeof va === 'string') return sortDir * va.localeCompare(vb);
    return sortDir * ((va ?? -1e9) - (vb ?? -1e9));
  });
  const best = SUM[0], bestLocal = SUM.find(r => r.local);
  const w = warnings();
  $('#overview').innerHTML = `
    <div class="tiles">
      <div class="tile"><div class="v">${SUM.length}</div><div class="l">arms (latest run each)</div></div>
      <div class="tile"><div class="v">${exams.length}</div><div class="l">exams</div></div>
      <div class="tile"><div class="v">${nq}</div><div class="l">questions</div></div>
      <div class="tile"><div class="v">${docs.size}</div><div class="l">documents</div></div>
      <div class="tile ${fails ? 'bad' : ''}"><div class="v">${fails}</div><div class="l">failed exams</div></div>
      <div class="tile"><div class="v">${esc(best.arm)} · ${f2(best.qi)}</div><div class="l">highest index</div></div>
      ${bestLocal ? `<div class="tile"><div class="v">${esc(bestLocal.arm)} · ${f2(bestLocal.qi)}</div><div class="l">best local arm</div></div>` : ''}
    </div>
    ${w.length ? `<h2>Read before quoting numbers</h2><ul class="warns">${w.map(x => `<li>${x}</li>`).join('')}</ul>` : ''}
    <h2>Ranking</h2>
    <p class="note">Latest run per arm. Click a column to sort, an arm to open its exams; hover a header for its definition. Red = above the warning threshold. Dot plot scale: ${ciLo.toFixed(1)} – 1.0.</p>
    <div class="tw"><table><thead><tr>${COLS.map(c => `<th class="${c.nosort ? '' : 's'} ${c.l ? 'l' : ''}" data-k="${c.k}"${c.tip ? ` data-tip="${esc(c.tip)}"` : ''}>${esc(c.h)}${sortK === c.k ? (sortDir < 0 ? ' ↓' : ' ↑') : ''}</th>`).join('')}</tr></thead>
    <tbody>${rows.map((r, i) => `<tr>${COLS.map(c => `<td class="${c.l ? 'l' : ''}">${cell(c, r, i)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>
    <div style="margin-top:14px">
      <div class="card"><h3 style="margin-top:0">Quality vs time per exam</h3><p class="note">Up = better, left = faster. Hover a point for details, click it to open the arm's exams.</p><div id="scatter" style="max-width:900px"></div></div>
      <div class="card"><h3 style="margin-top:0">Metric heatmap</h3><p class="note">Darker = better, also in the ↓ (lower is better) columns. Judge scores are on a 1–5 scale.</p><div id="heat"></div></div>
    </div>`;
  document.querySelectorAll('#overview th.s').forEach(th => th.onclick = () => {
    const k = th.dataset.k; if (sortK === k) sortDir = -sortDir; else { sortK = k; sortDir = LOWER_BETTER.has(k) ? 1 : -1; }
    renderOverview();
  });
  $('#scatter').innerHTML = scatter();
  $('#heat').innerHTML = heatmap();
  bindLinks($('#overview'));
}
function scatter() {
  const pts = SUM.filter(r => r.qi != null && r.time_s);
  if (!pts.length) return '<div class="note">No timing data.</div>';
  const W = 640, H = 330, L = 44, R = 16, T = 14, B = 38;
  const tmin = Math.min(...pts.map(r => r.time_s / 60)), tmax = Math.max(...pts.map(r => r.time_s / 60));
  const x0 = Math.log10(tmin / 1.5), x1 = Math.log10(tmax * 2.2);
  const y0 = Math.max(0, Math.floor(Math.min(...pts.map(r => r.qi)) * 10) / 10 - 0.05), y1 = 1.0;
  const X = t => L + (Math.log10(t) - x0) / (x1 - x0) * (W - L - R), Y = v => T + (y1 - v) / (y1 - y0) * (H - T - B);
  let g = '';
  [0.1, 0.3, 1, 3, 10, 30, 100, 300].filter(t => Math.log10(t) >= x0 && Math.log10(t) <= x1).forEach(t =>
    g += `<line x1="${X(t)}" x2="${X(t)}" y1="${T}" y2="${H - B}" stroke="var(--grid)"/><text x="${X(t)}" y="${H - B + 15}" text-anchor="middle">${t}</text>`);
  for (let v = Math.ceil(y0 * 10) / 10; v <= y1 + 1e-9; v += 0.1)
    g += `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--grid)"/><text x="${L - 6}" y="${Y(v) + 4}" text-anchor="end">${v.toFixed(1)}</text>`;
  g += `<text x="${(L + W - R) / 2}" y="${H - 6}" text-anchor="middle">median minutes per exam (log scale)</text>`;
  g += `<text transform="translate(12 ${(T + H - B) / 2}) rotate(-90)" text-anchor="middle">quality index</text>`;
  const placed = [];
  let dots = '', labs = '';
  [...pts].sort((a, b) => b.qi - a.qi).forEach(r => {
    const cx = X(r.time_s / 60), cy = Y(r.qi), col = r.local ? 'var(--accent)' : 'var(--accent2)';
    placed.push({x: cx - 6, y: cy - 6, w: 12, h: 12});
    dots += `<g data-tip="${esc(`${r.arm} – ${r.description}\nindex ${f2(r.qi)} (CI ${f2(r.ci_lo)}–${f2(r.ci_hi)})\n${dur(r.time_s)} per exam · ${r.calls ?? '–'} LLM calls\n${r.local ? 'local' : 'server'} · ${r.n_docs} documents`)}" style="cursor:pointer" data-open="${esc(r.run)}">
      <circle cx="${cx}" cy="${cy}" r="12" fill="transparent"/>
      <circle cx="${cx}" cy="${cy}" r="5" fill="${r.local ? col : 'var(--panel)'}" stroke="${col}" stroke-width="2"/></g>`;
  });
  [...pts].sort((a, b) => b.qi - a.qi).forEach(r => {
    const cx = X(r.time_s / 60), cy = Y(r.qi), w = r.arm.length * 7 + 2;
    for (const [dx, dy] of [[8, 0], [-8 - w, 0], [8, -11], [8, 11], [-8 - w, -11], [-8 - w, 11], [8, -22], [8, 22]]) {
      const box = {x: cx + dx, y: cy + dy - 8, w, h: 12};
      if (box.x < L || box.x + w > W) continue;
      if (!placed.some(p => box.x < p.x + p.w && p.x < box.x + box.w && box.y < p.y + p.h && p.y < box.y + box.h)) {
        placed.push(box); labs += `<text class="lab" x="${box.x}" y="${box.y + 10}">${esc(r.arm)}</text>`; break;
      }
    }
  });
  return `<div class="legend"><span><span class="sw" style="background:var(--accent)"></span>local model</span><span><span class="sw" style="border:2px solid var(--accent2);box-sizing:border-box"></span>university server</span></div>
    <svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Quality index against minutes per exam">${g}${dots}${labs}</svg>`;
}
const HEAT = [
  ['format_compliant', 'Format', 1], ['grounding_rate', 'Grounded', 1], ['blind_answerability', 'Blind', 1],
  ['distractor_validity', 'Distr.', 1], ['dup_share', 'Dupl. ↓', -1], ['nonq_share', 'Not Q ↓', -1],
  ['meta_reference_rate', '"Text" ↓', -1], ['coverage', 'Coverage', 1], ['recall@3', 'Recall@3', 1],
  ['judge_correctness', 'Correct', 5], ['judge_clarity', 'Clarity', 5], ['judge_distractor_quality', 'Distr. q', 5], ['judge_bloom_fit', 'Bloom', 5],
];
function heatmap() {
  const good = (v, s) => v == null ? null : s === 5 ? (v - 1) / 4 : s < 0 ? 1 - Math.min(1, v / 0.5) : v;
  return `<div class="tw" style="border:0"><table class="hm"><thead><tr><th class="l">Arm</th>${HEAT.map(h => `<th>${esc(h[1])}</th>`).join('')}</tr></thead><tbody>
    ${SUM.map(r => `<tr><td class="l"><a href="#" data-open="${esc(r.run)}">${esc(r.arm)}</a></td>${HEAT.map(([k, lab, s]) => {
      const v = r[k], g = good(v, s), txt = v == null ? '–' : s === 5 ? v.toFixed(1) : pct(v);
      return `<td style="background:${g == null ? 'transparent' : shade(g)}" data-tip="${esc(`${r.arm} · ${lab}: ${txt}`)}">${txt}</td>`;
    }).join('')}</tr>`).join('')}</tbody></table></div>`;
}

/* ================= DOCUMENTS ================= */
let docSel = null;
function docList() {
  const all = new Set();
  Object.values(PERDOC).forEach(m => Object.keys(m).forEach(d => all.add(d)));
  RUNS.filter(r => r.latest).forEach(r => r.exams.forEach(e => all.add(e.doc_id)));
  return [...all].sort((a, b) => ((DOCS[a] || {}).language || '').localeCompare((DOCS[b] || {}).language || '') || a.localeCompare(b));
}
function renderDocuments() {
  const docs = docList(), lo = 0.4;
  const colMean = arm => { const v = Object.values(PERDOC[arm] || {}).filter(x => x != null); return v.length ? v.reduce((a, b) => a + b) / v.length : null; };
  $('#documents').innerHTML = `
    <h2>Quality index per document</h2>
    <p class="note">Latest run per arm, mean over seeds. A dot = the arm did not run on that document. Click a cell to open the exam, a document name to see its chunking and what retrieval returned.</p>
    <div class="tw"><table class="hm"><thead><tr><th class="l">Document</th><th>Lang</th><th>Chars</th>${ARMS.map(a => `<th data-tip="${esc((sumOf(a) || {}).description || '')}">${esc(a)}</th>`).join('')}</tr></thead><tbody>
    ${docs.map(d => { const info = DOCS[d] || {}; return `<tr><td class="l"><a href="#" data-doc="${esc(d)}">${d === docSel ? '<b>' + esc(d) + '</b>' : esc(d)}</a></td><td>${esc(info.language || '')}</td><td>${info.chars ? info.chars.toLocaleString('en') : '–'}</td>
      ${ARMS.map(a => { const v = (PERDOC[a] || {})[d]; if (v == null) return '<td class="muted">·</td>';
        return `<td class="c" style="background:${shade((v - lo) / (1 - lo))}" data-exam="${esc(latestRun(a).id)}|${esc(d)}|" data-tip="${esc(`${a} on ${d}: ${f2(v)}`)}">${f2(v)}</td>`; }).join('')}</tr>`; }).join('')}
    <tr><td class="l"><b>Mean</b></td><td></td><td></td>${ARMS.map(a => `<td><b>${f2(colMean(a))}</b></td>`).join('')}</tr>
    </tbody></table></div>
    <div id="docdetail"></div>`;
  document.querySelectorAll('#documents [data-doc]').forEach(a => a.onclick = ev => { ev.preventDefault(); docSel = a.dataset.doc; renderDocuments(); setHash(); $('#docdetail').scrollIntoView({behavior: 'smooth'}); });
  bindLinks($('#documents'));
  if (docSel) renderDocDetail(docSel);
}
function renderDocDetail(d) {
  const info = DOCS[d] || {};
  const rows = RUNS.filter(r => r.latest).map(r => ({r, e: r.exams.find(e => e.doc_id === d)})).filter(x => x.e);
  $('#docdetail').innerHTML = `<h2>${esc(d)}</h2>
    <div class="row" style="margin-bottom:8px">${chip(info.language || '?')}${chip(info.subject || '?')}${chip(info.difficulty || '?')}${chip((info.chars || 0).toLocaleString('en') + ' characters')}</div>
    <p class="note">How each arm cut the document and what retrieval handed to the generator (first seed; hover a chunk for its text). Red = under 50 characters.</p>
    <div class="tw"><table><thead><tr><th class="l">Arm</th><th>Chunks</th><th>Median chars</th><th>&lt; 50 chars</th><th>&lt; 200 chars</th><th>Index</th><th class="l">Top retrieved chunks</th></tr></thead><tbody>
    ${rows.map(({r, e}) => { const c = e.chunks || {}, v = (PERDOC[r.arm] || {})[d];
      return `<tr><td class="l"><a href="#" data-exam="${esc(r.id)}|${esc(d)}|${e.seed}">${esc(r.arm)}</a></td><td>${c.n ?? '–'}</td><td>${c.median != null ? Math.round(c.median) : '–'}</td>
      <td class="${c.tiny ? 'flagv' : ''}">${c.tiny ?? '–'}</td><td>${c.small ?? '–'}</td><td>${f2(v)}</td>
      <td class="l" style="white-space:normal;min-width:320px">${e.retrieved.slice(0, 3).map(x => `<span class="chip ${x.len < 50 ? 'no' : ''}" data-tip="${esc(x.text)}">${esc(x.text.slice(0, 34))}${x.text.length > 34 ? '…' : ''} <span class="muted">(${x.len})</span></span>`).join(' ') || '<span class="muted">– (whole document)</span>'}</td></tr>`; }).join('')}
    </tbody></table></div>
    ${info.text ? `<details><summary>Document text${info.truncated ? ' (first ' + info.text.length.toLocaleString('en') + ' characters)' : ''}</summary><div class="src" style="max-height:480px">${esc(info.text)}</div></details>` : ''}`;
  bindLinks($('#docdetail'));
}

/* ================= COMPARE ================= */
let cmpA = ARMS.includes('E0') ? 'E0' : ARMS[ARMS.length - 1];
let cmpB = (SUM.find(r => r.local && r.arm !== cmpA) || SUM[0] || {}).arm;
function docMetric(arm, doc, col) {
  const r = latestRun(arm); if (!r) return null;
  const v = r.exams.filter(e => e.doc_id === doc && e.status !== 'error' && e.metrics)
    .map(e => col === 'qi' ? e.qi : col === 'dup_share' ? e.n_dup / Math.max(1, e.questions.length) : col === 'nonq_share' ? e.n_nonq / Math.max(1, e.questions.length) : e.metrics[col])
    .filter(x => x != null);
  return v.length ? v.reduce((a, b) => a + b) / v.length : null;
}
function wilcoxon(diffs) {
  const nz = diffs.filter(x => Math.abs(x) > 1e-12), n = nz.length;
  if (!n) return {n: 0, p: 1, r: 0};
  const abs = nz.map(Math.abs), idx = abs.map((_, i) => i).sort((a, b) => abs[a] - abs[b]), rank = new Array(n);
  for (let i = 0; i < n;) { let j = i; while (j + 1 < n && Math.abs(abs[idx[j + 1]] - abs[idx[i]]) < 1e-12) j++; for (let k = i; k <= j; k++) rank[idx[k]] = (i + j) / 2 + 1; i = j + 1; }
  const T = n * (n + 1) / 2, wp = nz.reduce((s, x, i) => s + (x > 0 ? rank[i] : 0), 0), obs = Math.min(wp, T - wp);
  const r2 = rank.map(r => Math.round(r * 2)), tot = r2.reduce((a, b) => a + b, 0), dist = new Float64Array(tot + 1); dist[0] = 1;
  for (const r of r2) for (let s = tot; s >= r; s--) dist[s] += dist[s - r];
  let c = 0; for (let s = 0; s <= Math.round(obs * 2); s++) c += dist[s];
  return {n, p: Math.min(1, 2 * c / 2 ** n), r: (2 * wp - T) / T};
}
function renderCompare() {
  if (ARMS.length < 2) { $('#compare').innerHTML = '<div class="empty">Need at least two scored arms.</div>'; return; }
  const opts = sel => ARMS.map(a => `<option ${a === sel ? 'selected' : ''}>${esc(a)}</option>`).join('');
  const dA = Object.keys(PERDOC[cmpA] || {}), dB = new Set(Object.keys(PERDOC[cmpB] || {}));
  const rows = dA.filter(d => dB.has(d)).sort().map(d => ({d, a: PERDOC[cmpA][d], b: PERDOC[cmpB][d]})).filter(x => x.a != null && x.b != null);
  const diffs = rows.map(x => x.b - x.a), w = wilcoxon(diffs);
  const mean = v => v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
  const wins = diffs.filter(x => x > 1e-9).length, loss = diffs.filter(x => x < -1e-9).length;
  const onlyA = dA.filter(d => !dB.has(d)), onlyB = [...dB].filter(d => !dA.includes(d));
  const MET = [['qi', 'Quality index', 0], ...HEAT.map(h => [h[0], h[1], h[2]])];
  const ida = latestRun(cmpA).id, idb = latestRun(cmpB).id;
  $('#compare').innerHTML = `
    <div class="row" style="margin-bottom:12px"><b>Reference</b> <select id="ca">${opts(cmpA)}</select> <b>vs new</b> <select id="cb">${opts(cmpB)}</select>
      <button class="btn" id="swap">⇄ swap</button></div>
    <p class="note">Paired on the documents both arms ran (per-document mean over seeds); differences are new − reference. p is the exact two-sided Wilcoxon signed-rank test, r the matched-pairs rank-biserial correlation (r &gt; 0: the new arm is better) – the same statistic as the report, without the Holm correction.</p>
    ${onlyA.length || onlyB.length ? `<ul class="warns"><li><b>Not the same documents.</b> Only ${esc(cmpA)}: ${esc(onlyA.join(', ') || '–')}. Only ${esc(cmpB)}: ${esc(onlyB.join(', ') || '–')}. Ignored below.</li></ul>` : ''}
    <div class="tiles">
      <div class="tile"><div class="v">${rows.length}</div><div class="l">common documents</div></div>
      <div class="tile"><div class="v">${f2(mean(rows.map(x => x.a)))} → ${f2(mean(rows.map(x => x.b)))}</div><div class="l">quality index</div></div>
      <div class="tile"><div class="v">${diffs.length ? (mean(diffs) >= 0 ? '+' : '') + f2(mean(diffs)) : '–'}</div><div class="l">mean difference</div></div>
      <div class="tile"><div class="v">${wins} / ${rows.length - wins - loss} / ${loss}</div><div class="l">docs better / equal / worse</div></div>
      <div class="tile ${rows.length && w.p >= 0.05 ? 'warn' : ''}"><div class="v">${rows.length ? w.p.toFixed(3) : '–'}</div><div class="l">Wilcoxon p (exact)</div></div>
      <div class="tile"><div class="v">${rows.length ? (w.r >= 0 ? '+' : '') + w.r.toFixed(2) : '–'}</div><div class="l">effect size r</div></div>
      <div class="tile"><div class="v">${w.n ? (2 / 2 ** w.n).toFixed(3) : '–'}</div><div class="l">smallest p possible (n = ${w.n})</div></div>
    </div>
    <div class="grid2">
      <div><h3>Per document</h3><div class="tw"><table><thead><tr><th class="l">Document</th><th>${esc(cmpA)}</th><th>${esc(cmpB)}</th><th>Difference</th><th></th></tr></thead><tbody>
      ${rows.map(x => { const d = x.b - x.a, wpx = Math.min(80, Math.abs(d) * 160);
        return `<tr><td class="l">${esc(x.d)} <span class="muted">${esc((DOCS[x.d] || {}).language || '')}</span></td>
        <td><a href="#" data-exam="${esc(ida)}|${esc(x.d)}|">${f2(x.a)}</a></td><td><a href="#" data-exam="${esc(idb)}|${esc(x.d)}|">${f2(x.b)}</a></td>
        <td class="${d < -1e-9 ? 'flagv' : ''}">${d >= 0 ? '+' : ''}${f2(d)}</td>
        <td><svg width="170" height="12"><line x1="85" x2="85" y1="0" y2="12" stroke="var(--ink3)"/><rect x="${d >= 0 ? 85 : 85 - wpx}" y="2" width="${wpx}" height="8" rx="2" fill="${d >= 0 ? 'var(--accent)' : 'var(--accent2)'}"/></svg></td></tr>`; }).join('')}
      </tbody></table></div></div>
      <div><h3>Per metric (common documents)</h3><div class="tw"><table><thead><tr><th class="l">Metric</th><th>${esc(cmpA)}</th><th>${esc(cmpB)}</th><th>Difference</th><th>p</th></tr></thead><tbody>
      ${MET.map(([k, lab, s]) => {
        const pairs = rows.map(x => [docMetric(cmpA, x.d, k), docMetric(cmpB, x.d, k)]).filter(p => p[0] != null && p[1] != null);
        if (!pairs.length) return '';
        const a = mean(pairs.map(p => p[0])), b = mean(pairs.map(p => p[1])), t = wilcoxon(pairs.map(p => p[1] - p[0])), dd = b - a;
        const raw = s === 5 || s === 0, fm = v => raw ? v.toFixed(2) : pct(v);
        const ds = raw ? (dd >= 0 ? '+' : '') + dd.toFixed(2) : (dd >= 0 ? '+' : '') + Math.round(dd * 100) + ' pp';
        const worse = s < 0 ? dd > 0.005 : dd < -0.005;
        return `<tr><td class="l">${esc(lab)}</td><td>${fm(a)}</td><td>${fm(b)}</td><td class="${worse ? 'flagv' : ''}">${ds}</td><td>${t.n ? t.p.toFixed(3) : '–'}</td></tr>`; }).join('')}
      </tbody></table></div><p class="note">↓ = lower is better. Red = the new arm is worse.</p></div>
    </div>`;
  $('#ca').onchange = () => { cmpA = $('#ca').value; renderCompare(); setHash(); };
  $('#cb').onchange = () => { cmpB = $('#cb').value; renderCompare(); setHash(); };
  $('#swap').onclick = () => { [cmpA, cmpB] = [cmpB, cmpA]; renderCompare(); setHash(); };
  bindLinks($('#compare'));
}

/* ================= EXAMS ================= */
let run = null, exam = null, mode = 'paper', answers = false;
const L10N = {
  hu: {exam: 'Feladatlap', name: 'Név', date: 'Dátum', score: 'Pontszám', inst: 'Minden kérdésnél egy helyes választ jelöljön meg.', key: 'Megoldókulcs', doc: 'Forrás', q: 'kérdés'},
  en: {exam: 'Exam', name: 'Name', date: 'Date', score: 'Score', inst: 'Choose the one correct answer for each question.', key: 'Answer key', doc: 'Source', q: 'questions'},
};
function isProblem(q) {
  return q.grounded === false || q.blind_correct === false || q.verified === false || q.meta_reference || q.key_in_stem ||
         q.dup_of != null || q.is_question === false || (q.judge_correctness != null && q.judge_correctness <= 2) || q.judge_error;
}
function examSummary(e) {
  const qs = e.questions, n = qs.length;
  const g = qs.filter(q => q.grounded != null), b = qs.filter(q => q.blind_correct != null);
  return {n, grounded: g.length ? g.filter(q => q.grounded).length / g.length : null,
          blind: b.length ? b.filter(q => q.blind_correct).length / b.length : null, problems: qs.filter(isProblem).length};
}
function renderRuns() {
  const opt = r => `<option value="${RUNS.indexOf(r)}">${esc(r.arm)} · ${esc(r.id)}${r.scored ? '' : ' (not scored)'}</option>`;
  const old = RUNS.filter(r => !r.latest);
  $('#run').innerHTML = `<optgroup label="Latest run per arm">${RUNS.filter(r => r.latest).map(opt).join('')}</optgroup>${old.length ? `<optgroup label="Older runs">${old.map(opt).join('')}</optgroup>` : ''}`;
  $('#run').onchange = () => { run = RUNS[+$('#run').value]; exam = run.exams[0] || null; renderExams(); renderMain(); setHash(); };
  if (!run && RUNS.length) run = SUM.length ? latestRun(SUM[0].arm) : RUNS[RUNS.length - 1];
}
function renderExams() {
  if (!run) { $('#exams').innerHTML = '<div class="stat">No runs found.</div>'; return; }
  $('#run').value = RUNS.indexOf(run);
  $('#rundesc').textContent = `${run.description || ''} · ${run.generator}`;
  $('#exams').innerHTML = run.exams.map((e, i) => {
    const s = examSummary(e), st = e.status !== 'ok' ? ` · <b style="color:var(--bad)">${esc(e.status)}</b>` : '';
    return `<button class="exam ${exam === e ? 'on' : ''}" data-i="${i}">${esc(e.doc_id)} · seed ${e.seed}${st}
      <small>index ${f2(e.qi)} · ${s.n}/${e.n_requested ?? '?'} q · grounded ${pct(s.grounded)} · ${s.problems} flagged${e.n_dup ? ` · ${e.n_dup} repeated` : ''}</small></button>`;
  }).join('');
  document.querySelectorAll('#exams .exam').forEach(b => b.onclick = () => { exam = run.exams[+b.dataset.i]; renderExams(); renderMain(); setHash(); });
}
function tiles(e) {
  const m = e.metrics || {}, c = e.chunks || {}, n = e.questions.length;
  const t = (v, l, cls = '', tipx = '') => `<div class="tile ${cls}"${tipx ? ` data-tip="${esc(tipx)}"` : ''}><div class="v">${v}</div><div class="l">${l}</div></div>`;
  const stages = e.calls_by_stage ? Object.entries(e.calls_by_stage).map(([k, v]) => `${k}: ${v}`).join('\n') : '';
  return `<div class="tiles">${[
    t(f2(e.qi), 'quality index'), t(pct(m.grounding_rate), 'grounded'), t(pct(m.blind_answerability), 'blind-solvable'),
    t(pct(m.distractor_validity), 'good distractors'),
    t(`${e.n_dup}/${n}`, 'repeated questions', e.n_dup ? 'bad' : ''), t(`${e.n_nonq}/${n}`, 'not a question', e.n_nonq ? 'warn' : ''),
    t(pct(m.coverage), 'coverage'), t(pct(m['recall@3']), 'retrieval recall@3'),
    t(dur(e.total_s), 'time'), t(e.calls ?? '–', 'LLM calls', '', stages),
    t(e.vram != null ? (e.vram / 1024).toFixed(1) + ' GB' : '–', 'VRAM peak'),
    t(c.n != null ? `${c.n} · ${Math.round(c.median)}` : '–', 'chunks · median chars', c.tiny ? 'bad' : '', c.n != null ? `${c.tiny} chunks under 50 characters, ${c.small} under 200, longest ${c.max}` : ''),
  ].join('')}</div>`;
}
function renderPaper(e, qs) {
  const L = L10N[e.language] || L10N.en, keys = [];
  const body = qs.map(([q, n]) => {
    const opts = q.options || [], k = opts.findIndex(o => o.correct);
    keys.push(`${n}. ${k >= 0 ? LETTERS[k] : esc(q.key || '–')}`);
    const flags = [q.dup_of != null ? `repeats Q${q.dup_of + 1}` : '', q.is_question === false ? 'not a question' : ''].filter(Boolean).join(' · ');
    return `<li value="${n}"><div class="ps">${esc(q.text)}${flags ? `<span class="pflag">${esc(flags)}</span>` : ''}</div>
      ${opts.length ? `<div class="po">${opts.map((o, i) => `<div class="opt ${answers && o.correct ? 'right' : ''}"><span class="bub">${LETTERS[i]}</span><span>${esc(o.text)}</span></div>`).join('')}</div>`
        : `<div class="lines"></div><div class="lines"></div>${answers && q.key ? `<div class="opt right">${esc(q.key)}</div>` : ''}`}</li>`;
  }).join('');
  return `<article class="paper">
    <div class="pt">${esc(L.exam)}${e.subject ? ' – ' + esc(e.subject) : ''}</div>
    <div class="pm">${esc(L.doc)}: ${esc(e.doc_id)} · ${esc(run.arm)}, seed ${e.seed} · ${qs.length} ${L.q}</div>
    <div class="pn"><span>${L.name}: ______________________________</span><span>${L.date}: ______________</span><span>${L.score}: ____ / ${qs.length}</span></div>
    <p class="pi">${L.inst}</p>
    <ol class="pq">${body}</ol>
    ${answers ? `<div class="akey"><b>${L.key}:</b> ${keys.map(k => `<span>${k}</span>`).join('')}</div>` : ''}
  </article>`;
}
function renderQuestion(q, n) {
  const opts = (q.options || []).map(o => `<li class="${o.correct ? 'key' : ''}">${esc(o.text)}${o.correct ? ' ✓' : ''}</li>`).join('');
  const scores = ['correctness', 'clarity', 'distractor_quality', 'bloom_fit']
    .map(k => q['judge_' + k] == null ? '' : chip(`${k.replace('_', ' ')} ${q['judge_' + k]}/5`, q['judge_' + k] >= 4 ? 'ok' : q['judge_' + k] <= 2 ? 'no' : 'mid')).join('');
  return `<div class="q ${isProblem(q) ? 'flag' : ''}">
    <div class="row"><b>${n}.</b>${chip(q.type)}${q.bloom ? chip(q.bloom) : ''}
      ${yesno(q.grounded, 'grounded', 'not grounded')}${yesno(q.blind_correct, 'blind ✓', 'blind ✗')}
      ${q.verified == null ? '' : yesno(q.verified, 'verified', 'unverified')}
      ${q.dup_of != null ? chip('repeats Q' + (q.dup_of + 1), 'no') : ''}${q.is_question === false ? chip('not a question', 'mid') : ''}
      ${q.key_in_stem ? chip('answer in stem', 'no') : ''}${q.meta_reference ? chip('meta-reference', 'no') : ''}
      ${q.judge_would_use == null ? '' : yesno(q.judge_would_use, 'would use', 'would not use')}</div>
    <div class="qt">${esc(q.text)}</div>
    <ol type="A">${opts}</ol>
    <div class="row">${scores}</div>
    ${q.judge_rationale ? `<div class="why"><b>Judge:</b> ${esc(q.judge_rationale)}</div>` : ''}
    ${q.key_evidence ? `<div class="why"><b>Evidence quoted by the judge:</b> „${esc(q.key_evidence)}”</div>` : ''}
    ${q.judge_error ? `<div class="why" style="color:var(--bad)">Judge error: ${esc(q.judge_error)}</div>` : ''}
    <details><summary>Source text${q.citations && q.citations.length ? ' (cites ' + esc(q.citations.join(', ')) + ')' : ''}${q.concept ? ' · planned concept: ' + esc(q.concept) : ''}</summary>
      <div class="src">${esc(q.source) || '–'}</div></details>
  </div>`;
}
function renderMain() {
  if (!exam) { $('#main').innerHTML = '<div class="empty">Pick an exam on the left.</div>'; return; }
  const s = examSummary(exam), term = $('#find').value.trim().toLowerCase(), only = $('#problems').checked;
  let qs = exam.questions.map((q, i) => [q, i + 1]);
  if (only) qs = qs.filter(([q]) => isProblem(q));
  if (term) qs = qs.filter(([q]) => (q.text + ' ' + (q.options || []).map(o => o.text).join(' ')).toLowerCase().includes(term));
  const tinyCtx = exam.retrieved.slice(0, 3).some(c => c.len < 50);
  const head = `<div class="card head noprint"><h2>${esc(run.arm)} · ${esc(exam.doc_id)} · seed ${exam.seed}</h2>
    <div class="row">${chip(exam.status, exam.status === 'ok' ? 'ok' : 'no')}${chip(exam.language || '')}${chip(exam.difficulty || '')}
      ${chip(`${s.n}/${exam.n_requested ?? '?'} questions`, s.n === exam.n_requested ? 'ok' : 'no')}${chip(s.problems + ' flagged', s.problems ? 'mid' : 'ok')}
      <span style="flex:1"></span>
      <span class="seg"><button data-m="paper" class="${mode === 'paper' ? 'on' : ''}">Test paper</button><button data-m="review" class="${mode === 'review' ? 'on' : ''}">Review</button></span>
      ${mode === 'paper' ? `<label class="row" style="gap:5px;font-size:13px"><input type="checkbox" id="ans" ${answers ? 'checked' : ''}>Show answers</label><button class="btn" id="print">Print</button>` : ''}</div>
    <div class="stat" style="margin-top:6px">model ${esc(exam.model || '–')}${exam.unverified != null ? ' · ' + exam.unverified + ' unverified, ' + (exam.replacements ?? 0) + ' replaced by the verifier' : ''}</div>
    ${exam.error ? `<div class="why" style="color:var(--bad)">${esc(exam.error)}</div>` : ''}
    <div style="margin-top:12px">${tiles(exam)}</div>
    ${exam.retrieved.length ? `<details ${tinyCtx && mode === 'review' ? 'open' : ''}><summary>What retrieval gave the generator (${exam.retrieved.length} chunks)${tinyCtx ? ' – <b style="color:var(--bad)">tiny chunks!</b>' : ''}</summary>
      ${exam.retrieved.map(c => `<div class="ctx ${c.len < 50 ? 'tiny' : ''}"><span class="muted">#${c.rank ?? '?'} · chunk ${c.chunk ?? '?'} · ${c.len} chars</span>\n${esc(c.text)}</div>`).join('')}</details>` : ''}
  </div>`;
  const body = !qs.length ? '<div class="empty">No questions match.</div>' : mode === 'paper' ? renderPaper(exam, qs) : qs.map(([q, n]) => renderQuestion(q, n)).join('');
  $('#main').innerHTML = head + body;
  $('#main').querySelectorAll('.seg button').forEach(b => b.onclick = () => { mode = b.dataset.m; renderMain(); });
  if ($('#ans')) $('#ans').onchange = () => { answers = $('#ans').checked; renderMain(); };
  if ($('#print')) $('#print').onclick = () => window.print();
}
$('#find').oninput = renderMain; $('#problems').onchange = renderMain;
document.addEventListener('keydown', ev => {
  if (tab !== 'exams' || !run || ev.target.matches('input,select,textarea')) return;
  if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
  const i = run.exams.indexOf(exam), j = Math.max(0, Math.min(run.exams.length - 1, i + (ev.key === 'ArrowRight' ? 1 : -1)));
  if (j !== i) { exam = run.exams[j]; renderExams(); renderMain(); setHash(); ev.preventDefault(); }
});

/* ---------------- start ---------------- */
renderRuns();
function route() {
  const [t, ...rest] = location.hash.slice(1).split('/').map(decodeURIComponent);
  if (t === 'documents' && rest[0]) docSel = rest[0];
  if (t === 'compare' && rest.length === 2 && ARMS.includes(rest[0]) && ARMS.includes(rest[1])) [cmpA, cmpB] = rest;
  if (t === 'exams' && rest[0]) {
    run = RUNS.find(r => r.id === rest[0]) || run;
    exam = run && rest[1] ? run.exams.find(e => e.doc_id === rest[1] && String(e.seed) === rest[2]) || null : null;
  }
  if (run && !exam) exam = run.exams[0] || null;
  show(['overview', 'documents', 'compare', 'exams'].includes(t) ? t : (SUM.length ? 'overview' : 'exams'), false);
}
window.addEventListener('hashchange', route);
route();
</script>
</body>
</html>
"""
