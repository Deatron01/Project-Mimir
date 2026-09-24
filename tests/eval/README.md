# Mimir evaluation harness (TDK)

This harness measures how good Mimir's generated exams are, reproducibly, so the numbers can go
into the TDK paper. It works in three steps: **run** generates exams, **score** measures them,
**analyze** builds the tables and figures. The research questions, metrics and experiment plan
are in the TDK outline doc; this README covers how to run everything.

```
dataset/manifest.yaml ─► run (configs/E*.yaml) ─► results/<run_id>/exams.jsonl
                                   ─► score (metrics + LLM judge) ─► questions.jsonl, exam_metrics.csv
                                   ─► rate-export ─► teachers fill xlsx ─► rate-import ─► ratings.csv
                                   ─► analyze ─► analysis/<name>/summary.md, CSV tables, PNG figures
```

## Setup (Windows, once)

```powershell
cd tests\eval
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

The Mimir services must be running (`docker-compose up -d` from the repo root), and Ollama must have
the generator model pulled (`ollama pull qwen2.5:7b`; E2x also needs `ollama pull llama3.1:8b`). The
judge, E4/E4b and B-doc-S use the university GenAI server; the key comes from `OE_GENAI_API_KEY` in the
repo's `.env`.

Rebuild the changed services once (`docker-compose up -d --build runecarver bifrost heimdall`).
Service changes that the evaluation relies on:

- Bifrost's prompt lives in `services/bifrost/prompts.py` (text unchanged); the local fallback model
  is `OLLAMA_MODEL` (default `qwen2.5:7b`, as in the main README); the hard-coded error exam is now
  marked `metadata.is_fallback = true`.
- RuneCarver accepts `method` / `threshold_val` (cut rule) and `encoder` (`window` = fixed long-text
  encoder, default; `legacy` = old 512-token behaviour, only for E5a). It uses float32 on CPU.
- `tests/tester.py` polls `/status` for the async `/generate` and flags the fallback exam.

## Dataset

The pilot manifest has the 3 Hungarian test documents. Import the two public datasets once:

```powershell
python -m mimir_eval import eduqg              # 12 EN docs from OpenStax textbooks (downloads from GitHub)
python -m mimir_eval import milqa              # 24 HU docs from Hungarian Wikipedia (downloads from Hugging Face)
```

If the MILQA download is blocked, download `test.MILQA-2023-03-27.squad.s.json` from
https://huggingface.co/datasets/SzegedAI/MILQA/tree/main in a browser and run
`python -m mimir_eval import milqa --source path\to\test.MILQA-2023-03-27.squad.s.json`.
Both importers pick short / medium / long documents and keep only gold questions whose evidence
sentences are inside the document; see `dataset/README.md`. The EduQG part is already imported.

Check that everything is reachable:

```powershell
python -m mimir_eval check configs\e0_naive_local.yaml --judge-model gpt-oss:120b
```

## Running an experiment

```powershell
python -m mimir_eval run configs\e0_naive_local.yaml --max-docs 1     # smoke test first
python -m mimir_eval run configs\e0_naive_local.yaml                  # all documents x 3 seeds
python -m mimir_eval score results\E0_20261001_101500 --judge-model gpt-oss:120b
python -m mimir_eval analyze E0=results\E0_20261001_101500 --name e0-baseline
```

If some exams fail because a service or Ollama was down, rerun only those:
`python -m mimir_eval run configs\e0_naive_local.yaml --resume results\E0_20261001_101500`.

Comparing arms (e.g. baseline vs verifier, local vs server):

```powershell
python -m mimir_eval analyze E0=results\E0_... E2=results\E2_... E4=results\E4_... `
    --name main --compare E0 E2 --compare E0 E4
```

## Configs (one per experiment arm)

| File | Arm | What changes |
| --- | --- | --- |
| `b_doc_local.yaml` | B-doc-L | Status quo: the whole document in one prompt (same prompt as E0), `qwen2.5:7b`, 16k context; documents over 30,000 characters are cut and the cut share is recorded |
| `b_doc_server.yaml` | B-doc-S | The same on the GenAI server model (up to 80,000 characters) |
| `e0_naive_local.yaml` | E0 | Reference: production retrieval + production prompt, `qwen2.5:7b` on Ollama |
| `e0s_naive_service.yaml` | E0s | Whole chain through Bifrost `/generate`; smoke test only (Bifrost picks the model) |
| `e1_blueprint.yaml` | E1 | Planner + per-slot retrieval + one question per call, no verifier |
| `e2_blueprint_verifier.yaml` | E2 | E1 + verifier chain with retries ("Thorough") |
| `e2x_blueprint_other_verifier.yaml` | E2x | E2 with a verifier from another family (`llama3.1:8b` checks `qwen2.5:7b`) |
| `e2f_blueprint_fast.yaml` | E2f | E2 without the blind answer test ("Fast") |
| `e2h_blueprint_hybrid.yaml` | E2h | E2 with hybrid BM25 + dense retrieval |
| `e3_blueprint_graph.yaml` | E3 | E2 + concept graph |
| `e4_server_naive.yaml` | E4 | E0 on the GenAI server model (`qwen38udq8xl`) |
| `e4b_server_blueprint.yaml` | E4b | E2 on the GenAI server model |
| `e5a_chunk_legacy.yaml` | E5a | Old RuneCarver encoder (512-token bug), for before/after |
| `e5b_chunk_std.yaml` | E5b | Chunking: mean + 1.5·std cut rule |
| `e5c_chunk_fixed.yaml` | E5c | Chunking: fixed 800-character windows |

Every config inherits the defaults in `mimir_eval/config.py`; set only what differs. The full
resolved config, git commit and dataset version are saved in each run's `run.json`.

**Blueprint pipeline** (`mimir_eval/blueprint/`, ROADMAP section 5): a planner picks
`n + 3` concepts that cover the document; each slot gets a concept, a question type and a Bloom
level matched to the difficulty (easy: remember/understand; medium: understand/apply/analyze; hard:
apply/analyze/evaluate). For each slot it retrieves the concept's chunks plus the top-k search hits,
generates one question with chunk citations, and (E2+) verifies it: shape, meta-reference,
citations, then an LLM grounding + distractor check, then a blind answer test. A failed check goes
back to the generator as feedback (max 1 retry, a wider retrieval net when the key was not
supported), then one spare concept is tried, and as a last resort the best attempt is kept and marked
`verified: false`, so the question count is always met. The last resort prefers a well-formed attempt;
if none is, one repair call adds the missing options (`repair`), so a malformed question no longer
fails the whole exam. Two rule checks (`leakage_checks`) reject a stem that already contains the key
(at least 80 % of a key of three or more words) and an MCQ stem that is a statement, not a question.
`verifier_llm` runs the grounding and blind checks on another model (E2x). Near-duplicates (embedding similarity > 0.9)
are regenerated. E3 builds a session-scoped concept graph (one call per ~3,000 characters): graph
concepts replace the planner call, sibling concepts are offered as distractor ideas, and 1-hop
neighbour chunks join the context. Every run records calls per stage, retries, replacements and
unverified questions.

**Cost:** E0 makes 1 LLM call per exam; E2 makes roughly 3–5 calls per question (about 40–60 for 10
questions), and E3 adds the graph calls. Measure the real time per exam with
`--max-docs 1` first, then plan the full runs; the blueprint arms (one seed) on all documents are
overnight jobs on an 8 GB GPU. `--docs` and `--resume` let you split them across sessions.

## Running everything

`run_all.ps1` runs the whole matrix (check, run, score, analyze) in order and can be stopped and
restarted, because every step resumes:

```powershell
.\run_all.ps1                                   # all arms, judge gpt-oss:120b
.\run_all.ps1 -Arms E0,E2 -MaxDocs 2            # quick subset
```

## TDK report (Hungarian)

```powershell
python -m mimir_eval report --name pilot        # latest run of every arm -> report\pilot\
python -m mimir_eval view                        # results\viewer.html: read the generated exams
```

`report\<name>\` gets (PNG 300 dpi + PDF, and the text in `eredmenyek.md`):

| File | Content |
| --- | --- |
| `tabla1_osszesito` | ranking with the winner |
| `tabla2_gyoztes_vs_alap` | winner vs E0 |
| `tabla3_egyetertes` | judge-teacher agreement (Krippendorff α, Spearman ρ, Cohen κ); only when `ratings\ratings.csv` exists (`--ratings` for another path) |
| `tabla4_szignifikancia` | paired Wilcoxon for E1–E0, E2–E1, E3–E2, E4–E0, Holm-corrected p, rank-biserial r |
| `tabla5_nyelvek`, `abra7_nyelvek` | Hungarian vs English, per arm |
| `tabla6_adatkeszlet`, `adatkeszlet.csv` | documents, gold questions, lengths and licence per source |
| `abra1`–`abra6` | methods diagram, ranking, measures, cost, components, chunking |
| `peldak.md` | one good and one bad question per arm with the judge's reasoning (error analysis) |
| `latex/` | the paper's tables in English: `tab_main`, `tab_verifier` (judge outcomes by verifier verdict), `tab_verifier_arms` (precision, recall, κ of the verifier against the judge's "grounded"), `tab_leakage`, plus `fig_quality_time.dat` and `paper_numbers.json` |

With fewer than 6 documents everything is marked PILOT. Still to do (ROADMAP AI-19): freeze `eval-v1`,
full run, teacher rating.

**Speed settings (AI-18).** The judge sees only the chunks a question was written from (or the retrieved
context for E0) and runs gpt-oss with `Reasoning: low`; `score --judge-context document
--judge-reasoning none` restores the slower judge-v1 setup. Generators use `num_ctx` 8192, the verifier
retries once (`max_retries: 1`), the blueprint arms run one seed, and E4/E4b run on a fixed
12-document subset (6 HU + 6 EN) so they stay paired with E0/E2.

## What gets measured

| Metric | Source | Level |
| --- | --- | --- |
| Format compliance, valid JSON, shape | `schema.py` | exam |
| Grounding rate, distractor validity, 1–5 rubric scores | LLM judge (`judge.py`), sees the key | question |
| Blind answerability | LLM judge answers without the key | question |
| Meta-reference rate ("a szöveg szerint…") | regex, `schema.py` | question |
| Leakage rate (key in stem), non-question rate | token overlap / stem ending, `schema.py` | question |
| Truncated share of the document (B-doc) | `pipelines.py` | exam |
| Duplicate rate, section coverage, gold similarity | e5 embeddings, `metrics.py` | exam |
| Retrieval recall@k, MRR | gold evidence sentences vs retrieved chunks | exam |
| Time per step, peak VRAM, tokens, LLM calls | runner | exam |
| GPU name, total memory, driver (`run.json` → `hardware`); share of the Ollama model in GPU memory (`gpu_share`, from `/api/ps`) | `vram.py` | run / exam |

Exam statuses: `ok`; `parse_error` (model output not JSON) and `fallback` (Bifrost's hard-coded
"models overloaded" exam) count as failed exams; `error` (service or network down) is excluded
from the analysis and should be retried with `--resume`.

**Judge choice:** use a judge from a different model family than the generator (the default judge
is `gpt-oss:120b` when the generator is Qwen). `score` warns if they match. Judge answers are cached
in `judge_cache.jsonl`, so re-scoring is free.

**Statistics:** documents are the unit of analysis (mean over seeds and questions per document).
The harness reports 95% bootstrap CIs over documents, paired Wilcoxon tests with Holm correction,
and a rank-biserial effect size. With the Wilcoxon test, fewer than 6 paired documents can never
reach p < 0.05, so the 3 pilot documents are for checking the pipeline, not for claims.

## Teacher rating (RQ3)

```powershell
python -m mimir_eval rate-export results\E0_... results\E2_... results\E4_... --n-per-run 30 --raters 3
# send ratings\rater_A.xlsx, rater_B.xlsx, rater_C.xlsx; keep ratings\rating_key.csv to yourself
python -m mimir_eval rate-import ratings\rater_A.xlsx ratings\rater_B.xlsx ratings\rater_C.xlsx
python -m mimir_eval analyze E0=... E2=... E4=... --name human --ratings ratings\ratings.csv
```

Each rater gets the same items in a different order, with no pipeline labels. The sheet has a
Hungarian rubric (`rubric.py`, the same rubric the judge uses), a calibration tab, and 1–5
dropdown validation. The analysis reports Krippendorff's α per criterion, teacher means per arm,
Spearman ρ between judge and teachers, and Cohen's κ for judge "grounded" vs teacher correctness ≥ 4.

## Tests

```powershell
python -m pytest tests_unit -q
```

The end-to-end test runs the whole flow (run → score → rate → analyze) with fake services and a
mock LLM, so it needs neither Docker nor a GPU.

## Issues found and fixed

- The 2026-05-03 `tester.py` run did not measure the model: all three "1 question" results are
  Bifrost's hard-coded error exam. `tester.py` now polls `/status` and flags the fallback.
- RuneCarver embedded the whole text in one pass with `max_length=512`, so every sentence after
  about one page got a zero vector and cuts past that point came from the size limit, not from
  topic changes. The default encoder now works in <= 512-token windows (identical results on short
  texts; tested in `tests_unit/test_runecarver_window.py`). E5a keeps the old encoder for the
  before/after comparison.
- Bifrost's local fallback called `qwen2.5:14b` although the README targets `qwen2.5:7b` on 8 GB;
  it is now `OLLAMA_MODEL` (default 7b), in Bifrost and Heimdall.
