# Experiment plan: from the pilot to the main study

Status: **approved; code changes I1–I7 implemented and tested** (24 Sep 2026), decisions D1–D5 taken
with their defaults. Next: the runs R0–R5.

The paper (`main.tex`, "MIMIR: Verifiable, Privacy-Preserving Exam Generation with Local Language
Models") reports the pilot (`tests/eval/results_pilot`, `tests/eval/report_pilot`: one Hungarian
document, 3 seeds, 10 arms). The pilot answered no research question conclusively, but it showed
what the main study must change. Each item below comes from a pilot finding.

## 1. What the pilot showed

| # | Finding | Evidence | Consequence |
| --- | --- | --- | --- |
| F1 | Planning (E1) helps the 7B model | grounding 67→73 %, blind 85→93 %, distractors 80→87 %, coverage 50→58 % | Keep; confirm on 39 documents |
| F2 | The server model (E4) scores highest but clusters its questions | index 0.99, coverage 25 % (1 of 4 chunks) | Report coverage next to quality; add the whole-document baseline |
| F3 | The self-verifier (same 7B model) does not agree with the judge | passed: 66 % grounded, flagged: 75 % grounded (120 questions) | Validate the verifier as a classifier; try a different-family verifier |
| F4 | Last-resort questions can be malformed | 1 of 3 exams in E2, E2f, E2h, E3 had a 2–3-option question → format 0 | Fix the fallback |
| F5 | Answer leakage inflates metrics and the judge | key in stem: E3 20 %, E2h 10 %, E2f 7 %, E2 3 %; 47 % of E3 stems are not questions; judge gave them 5/5 | New rule checks and a leakage metric |
| F6 | Run-to-run noise ≈ 0.07 on one document | E0 and E5a had identical inputs: 0.83 vs 0.90 | 39 documents, document-level statistics |
| F7 | The local model fits 8 GB | GPU memory 1.6–1.9 GB idle → 7.0–7.8 GB peak; model + runtime 5.4–5.9 GB | Record GPU model and total memory in every run |

## 2. Code changes (before the main run) — all implemented

| # | Change | Where | Size |
| --- | --- | --- | --- |
| I1 | **Whole-document baseline** (`pipeline.kind: full_document`): the whole extracted document plus the request in one prompt, the "send the PDF to an LLM" status quo. Local run with a 16k context and documents cut at 30,000 characters (a 32k context does not fit next to a desktop on 8 GB; the pilot peaked at 7.8 GB with 16k), server run up to 80,000 characters; the cut share is recorded as `truncated_share` | `pipelines.py`, 2 new configs (B-doc-L, B-doc-S) | M |
| I2 | **Well-formed fallback:** the last-resort path keeps only questions that pass the shape check; if none does, it makes one repair call ("add the missing distractors") before giving up | `blueprint/pipeline.py` | S |
| I3 | **Leakage checks:** reject a question whose key is ≥80 % contained in the stem or whose stem is not a question; report `leakage_rate` and `non_question_rate` per exam | `schema.py`, `metrics.py`, verifier | S |
| I4 | **Verifier as a classifier:** report precision and recall of the verifier's pass/flag against the judge's "grounded" and the teachers' correctness | `analysis.py`, `report.py` | S |
| I5 | **Different-family verifier arm** (E2x): generator Qwen2.5-7B, verifier Llama-3.1-8B (both local; one model loaded at a time, so the verifier calls are batched per exam) | `blueprint/pipeline.py`, config | M |
| I6 | **Hardware record:** GPU name, total memory and driver in `run.json`; peak memory is already recorded | `runner.py`, `vram.py` | S |
| I7 | **Paper tables from the report:** `report` writes `tab_main.tex`, `tab_verifier.tex`, `tab_leakage.tex` and the plot data, so the paper `\input`s them | `report.py`, `paper/main.tex` | M |

S = up to half a day, M = one to two days. Every change has a mocked test (`tests/eval/tests_unit`).

Implementation notes:

- I1: `pipeline.kind: full_document`, configs `b_doc_local.yaml` and `b_doc_server.yaml`; same prompt
  as E0, only the context differs.
- I2: the last resort prefers well-formed attempts; if none is, one `[repair]` call adds the missing
  options (`repairs` / `repair_failed` in the exam record).
- I3: `leakage_checks` in the verifier (on by default, also without the LLM verifier); metrics
  `leakage_rate` and `non_question_rate`; keys shorter than three words are exempt.
- I4: `tab_verifier.tex` (judge outcomes by verdict) and `tab_verifier_arms.tex` (precision, recall,
  Cohen's κ per arm). On the pilot: κ from −0.14 to 0.07, i.e. chance level. Agreement with the teachers
  comes from the existing judge–teacher analysis once ratings exist.
- I5: `verifier_llm` in the config, `e2x_blueprint_other_verifier.yaml` (Llama-3.1-8B).
- I6: `run.json` → `hardware` (GPU name, memory, driver); every Ollama exam records `/api/ps`, and
  `gpu_share` < 1 in `exam_metrics.csv` means the model spilled to the CPU.
- I7: `report` writes `latex/` (`tab_main`, `tab_verifier`, `tab_verifier_arms`, `tab_leakage`,
  `tab_significance`, `fig_quality_time.dat`, `paper_numbers.json`); the paper's Tables VI and VII now
  come from it. Regenerating them from the pilot corrected three numbers in the draft: E3's time
  (8.0, not 8.1 min) and the blind answer rates in Table VII (89/79 %, not 81/77 %, because
  unanswerable blind attempts are now excluded as in every other table).

## 3. Arms for the main study

| Arm | What | Seeds | Why |
| --- | --- | --- | --- |
| B-doc-L / B-doc-S | Whole document in one prompt, local / server | 3 / 3 | The status quo the paper argues against (P1, P2) |
| E0 | Naive RAG (local) | 3 | Baseline |
| E1 | Blueprint | 1 | Effect of planning |
| E2 | Blueprint + self-verifier (with I2, I3) | 1 | Effect of verification |
| E2x | Blueprint + different-family verifier | 1 | Is F3 about self-verification? |
| E3 | E2 + concept graph | 1 | Graph |
| E4 / E4b | Server model: naive / blueprint + verifier | 3 / 1 | Local vs server |
| E5a | Legacy encoder | 3 | Effect of the chunker fix; only meaningful on documents longer than 512 tokens |

E2f, E2h, E5b and E5c stay in the harness but are optional for the paper.

## 4. Runs

| Step | What | Where | Rough time |
| --- | --- | --- | --- |
| R0 | Smoke test of every arm on 2 documents, including one long document | local GPU + server | 2–3 h |
| R1 | Local arms on all 39 documents | local GPU | 2–3 days (the blueprint arms are the slow ones, about 5–8 min per exam) |
| R2 | Server arms on all 39 documents | university server | about 1 day (the pilot's server median was 6.6 min per exam) |
| R3 | Scoring with the judge | university server | about 1 day |
| R4 | Teacher rating: 3 teachers, 15 questions × 4 core arms (B-doc-S, E0, E1, E2 or E2x) = 60 each, plus 10 calibration items | teachers | 1–2 weeks elapsed |
| R5 | `report` → paper tables, results text | — | 1–2 days |

Every step resumes after an interruption; R1 and R2 can run in parallel.

## 5. Decisions needed

| # | Question | Default if no answer |
| --- | --- | --- |
| D1 | Which GPU ran the pilot, and will the main run use the same one? The paper needs the model name. | Same GPU; name to be filled in (new runs record it) |
| D2 | What is the server model `qwen38udq8xl` (name and size)? | Keep it; name and size to be filled in |
| D3 | Is the different-family verifier arm (E2x, Llama-3.1-8B) worth adding? | Yes |
| D4 | Teacher rating as in R4 (3 teachers, 60 questions each)? | Yes |
| D5 | Target venue and deadline? | IEEE conference format, 6 pages |
