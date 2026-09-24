"""`view`: one self-contained HTML page for reading generated exams by eye.

    python -m mimir_eval view            -> results/viewer.html (all runs under results/)

The page embeds the data (no server, no internet): pick a run and an exam on the left, read the
questions with the correct answer highlighted, the judge's verdicts and the source text they came
from. "Only problems" hides questions that passed every check.
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import resolve
from .scoring import latest_exams
from .util import read_jsonl

SOURCE_CHARS = 2500      # per question, so the page stays small even for long documents


def _source(exam: dict, q: dict) -> str:
    chunks = exam.get("chunks") or []
    ids = [i for i in (q.get("context_ids") or []) if isinstance(i, int) and 0 <= i < len(chunks)]
    if ids:
        text = "\n\n".join(chunks[i] for i in ids)
    else:
        text = exam.get("context_text") or ""
    return text[:SOURCE_CHARS] + ("…" if len(text) > SOURCE_CHARS else "")


def collect(results_root: Path) -> list[dict]:
    runs = []
    for rd in sorted(p for p in results_root.iterdir() if (p / "exams.jsonl").exists()):
        meta = json.loads((rd / "run.json").read_text(encoding="utf-8")) if (rd / "run.json").exists() else {}
        cfg = meta.get("config", {})
        judged = {q["uid"]: q for q in read_jsonl(rd / "questions.jsonl")}
        exams = []
        for ex in sorted(latest_exams(read_jsonl(rd / "exams.jsonl")), key=lambda e: (e["doc_id"], e["seed"])):
            qs = []
            for q in ex.get("questions", []):
                j = judged.get(f"{ex['run_id']}|{ex['doc_id']}|{ex['seed']}|{q['qid']}", {})
                qs.append({
                    "qid": q["qid"], "type": q["type"], "text": q["text"], "options": q["options"],
                    "bloom": q.get("bloom"), "citations": q.get("citations"), "verified": q.get("verified"),
                    "concept": q.get("planned_concept"), "source": _source(ex, q),
                    **{k: j.get(k) for k in ("grounded", "blind_correct", "meta_reference", "judge_correctness",
                                             "judge_clarity", "judge_distractor_quality", "judge_bloom_fit",
                                             "judge_would_use", "judge_rationale", "key_evidence",
                                             "distractor_valid_rate", "judge_bloom_level", "judge_error")},
                })
            t = ex.get("timings") or {}
            exams.append({
                "doc_id": ex["doc_id"], "seed": ex["seed"], "status": ex.get("status"),
                "language": ex.get("language"), "difficulty": ex.get("difficulty"),
                "error": ex.get("error") or ex.get("parse_error"), "model": ex.get("model_used"),
                "n_requested": ex.get("n_requested"), "total_s": t.get("total_s"),
                "calls": (ex.get("llm") or {}).get("calls"), "questions": qs,
                "unverified": (ex.get("blueprint") or {}).get("unverified"),
            })
        runs.append({"id": rd.name, "arm": cfg.get("name", rd.name), "description": cfg.get("description", ""),
                     "scored": (rd / "questions.jsonl").exists(), "exams": exams})
    return runs


def build_viewer(results_root: str = "results", out: str | None = None) -> Path:
    root = resolve(results_root)
    runs = collect(root)
    out_path = resolve(out) if out else root / "viewer.html"
    data = json.dumps(runs, ensure_ascii=False).replace("</", "<\\/")
    out_path.write_text(TEMPLATE.replace("__DATA__", data), encoding="utf-8")
    n = sum(len(r["exams"]) for r in runs)
    print(f"[view] {len(runs)} runs, {n} exams -> {out_path}")
    return out_path


TEMPLATE = r"""<!doctype html>
<html lang="hu">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mimir exam viewer</title>
<style>
:root{--bg:#f7f7f5;--panel:#fff;--ink:#1b1b19;--ink2:#5b5a55;--line:#e3e2dc;--accent:#2a78d6;
--good:#1f7a3a;--goodbg:#e6f4ea;--bad:#b3261e;--badbg:#fbe9e7;--warn:#8a5a00;--warnbg:#fdf3dc;--key:#e6f4ea}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--panel:#1f1f1d;--ink:#f2f1ec;--ink2:#b3b1a8;--line:#34332f;
--accent:#6aa6f0;--good:#7fd29a;--goodbg:#1d3325;--bad:#f28b82;--badbg:#3a1f1d;--warn:#f0c46a;--warnbg:#3a3018;--key:#1d3325}}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--ink)}
.app{display:grid;grid-template-columns:300px 1fr;height:100vh}
aside{border-right:1px solid var(--line);background:var(--panel);overflow:auto;padding:14px}
main{overflow:auto;padding:20px 28px}
h1{font-size:16px;margin:0 0 10px}label{display:block;font-size:12px;color:var(--ink2);margin:12px 0 4px}
select,input[type=search]{width:100%;padding:7px 8px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);font:inherit}
.exam{display:block;width:100%;text-align:left;padding:7px 9px;margin:3px 0;border:1px solid transparent;border-radius:8px;background:none;color:var(--ink);cursor:pointer;font:inherit;font-size:13px}
.exam:hover{background:var(--bg)}.exam.on{border-color:var(--accent);background:var(--bg)}
.exam small{color:var(--ink2);display:block}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.chip{font-size:12px;padding:2px 8px;border-radius:999px;border:1px solid var(--line);color:var(--ink2);white-space:nowrap}
.ok{background:var(--goodbg);color:var(--good);border-color:transparent}.no{background:var(--badbg);color:var(--bad);border-color:transparent}
.mid{background:var(--warnbg);color:var(--warn);border-color:transparent}
.head{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:16px}
.head h2{margin:0 0 6px;font-size:18px}.stat{font-size:13px;color:var(--ink2)}
.q{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:12px}
.q.flag{border-left:4px solid var(--bad)}
.qt{font-weight:600;margin:6px 0 8px}
ol{margin:0 0 8px;padding-left:22px}li{padding:3px 6px;border-radius:6px;margin:2px 0}li.key{background:var(--key);font-weight:600}
details{margin-top:8px}summary{cursor:pointer;color:var(--ink2);font-size:13px}
.src{white-space:pre-wrap;font-size:13px;background:var(--bg);border-radius:8px;padding:10px;margin-top:6px;max-height:320px;overflow:auto}
.why{font-size:13px;color:var(--ink2);margin-top:6px}.empty{color:var(--ink2);padding:40px 0}
.toggle{display:flex;gap:6px;align-items:center;font-size:13px;margin-top:12px}
@media (max-width:760px){.app{grid-template-columns:1fr;height:auto}aside{border-right:0;border-bottom:1px solid var(--line)}}
</style>
</head>
<body>
<div class="app">
<aside>
  <h1>Mimir exam viewer</h1>
  <label for="run">Run (arm)</label><select id="run"></select>
  <div class="stat" id="rundesc"></div>
  <label for="find">Search questions</label><input id="find" type="search" placeholder="word in a question or answer">
  <div class="toggle"><input type="checkbox" id="problems"><label for="problems" style="margin:0">Only problems</label></div>
  <label>Exams</label><div id="exams"></div>
</aside>
<main id="main"><div class="empty">Pick a run and an exam on the left.</div></main>
</div>
<script id="data" type="application/json">__DATA__</script>
<script>
const RUNS = JSON.parse(document.getElementById('data').textContent);
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pct = v => v == null ? '–' : Math.round(v * 100) + '%';
let run = null, exam = null;

function isProblem(q) {
  return q.grounded === false || q.blind_correct === false || q.verified === false || q.meta_reference ||
         (q.judge_correctness != null && q.judge_correctness <= 2) || q.judge_error;
}
function chip(label, state) { return `<span class="chip ${state}">${esc(label)}</span>`; }
function yesno(v, yes, no) { return v == null ? '' : chip(v ? yes : no, v ? 'ok' : 'no'); }

function examSummary(e) {
  const qs = e.questions, n = qs.length;
  const g = qs.filter(q => q.grounded != null), b = qs.filter(q => q.blind_correct != null);
  return {n, grounded: g.length ? g.filter(q => q.grounded).length / g.length : null,
          blind: b.length ? b.filter(q => q.blind_correct).length / b.length : null,
          problems: qs.filter(isProblem).length};
}

function renderRuns() {
  $('#run').innerHTML = RUNS.map((r, i) => `<option value="${i}">${esc(r.arm)} · ${esc(r.id)}${r.scored ? '' : ' (not scored)'}</option>`).join('');
  $('#run').onchange = () => { run = RUNS[+$('#run').value]; exam = null; renderExams(); renderMain(); };
  if (RUNS.length) { run = RUNS[RUNS.length - 1]; $('#run').value = RUNS.length - 1; }
  renderExams(); renderMain();
}

function renderExams() {
  if (!run) { $('#exams').innerHTML = '<div class="stat">No runs found.</div>'; return; }
  $('#rundesc').textContent = run.description || '';
  $('#exams').innerHTML = run.exams.map((e, i) => {
    const s = examSummary(e);
    const st = e.status !== 'ok' ? ` · <b style="color:var(--bad)">${esc(e.status)}</b>` : '';
    return `<button class="exam ${exam === e ? 'on' : ''}" data-i="${i}">${esc(e.doc_id)} · seed ${e.seed}${st}
      <small>${s.n}/${e.n_requested ?? '?'} q · grounded ${pct(s.grounded)} · blind ${pct(s.blind)} · ${s.problems} flagged</small></button>`;
  }).join('');
  document.querySelectorAll('.exam').forEach(b => b.onclick = () => { exam = run.exams[+b.dataset.i]; renderExams(); renderMain(); });
}

function renderQuestion(q, n) {
  const opts = (q.options || []).map(o => `<li class="${o.correct ? 'key' : ''}">${esc(o.text)}${o.correct ? ' ✓' : ''}</li>`).join('');
  const scores = ['correctness', 'clarity', 'distractor_quality', 'bloom_fit']
    .map(k => q['judge_' + k] == null ? '' : chip(`${k.replace('_', ' ')} ${q['judge_' + k]}/5`, q['judge_' + k] >= 4 ? 'ok' : q['judge_' + k] <= 2 ? 'no' : 'mid')).join('');
  return `<div class="q ${isProblem(q) ? 'flag' : ''}">
    <div class="row"><b>${n}.</b>${chip(q.type)}${q.bloom ? chip(q.bloom) : ''}
      ${yesno(q.grounded, 'grounded', 'not grounded')}${yesno(q.blind_correct, 'blind ✓', 'blind ✗')}
      ${q.verified == null ? '' : yesno(q.verified, 'verified', 'unverified')}
      ${q.meta_reference ? chip('meta-reference', 'no') : ''}${q.judge_would_use == null ? '' : yesno(q.judge_would_use, 'would use', 'would not use')}</div>
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
  $('#main').innerHTML = `<div class="head"><h2>${esc(run.arm)} · ${esc(exam.doc_id)} · seed ${exam.seed}</h2>
    <div class="row">${chip(exam.status, exam.status === 'ok' ? 'ok' : 'no')}${chip(exam.language || '')}${chip(exam.difficulty || '')}
      ${chip(`${s.n}/${exam.n_requested ?? '?'} questions`, s.n === exam.n_requested ? 'ok' : 'no')}
      ${chip('grounded ' + pct(s.grounded))}${chip('blind ' + pct(s.blind))}${chip(s.problems + ' flagged', s.problems ? 'mid' : 'ok')}</div>
    <div class="stat" style="margin-top:6px">model ${esc(exam.model || '–')} · ${exam.total_s ? Math.round(exam.total_s) + ' s' : '–'} · ${exam.calls ?? '–'} LLM calls${exam.unverified != null ? ' · ' + exam.unverified + ' unverified' : ''}</div>
    ${exam.error ? `<div class="why" style="color:var(--bad)">${esc(exam.error)}</div>` : ''}</div>
    ${qs.length ? qs.map(([q, n]) => renderQuestion(q, n)).join('') : '<div class="empty">No questions match.</div>'}`;
}

$('#find').oninput = renderMain; $('#problems').onchange = renderMain;
renderRuns();
</script>
</body>
</html>
"""
