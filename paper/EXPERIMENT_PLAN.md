# Experiment plan: exam generation on consumer GPUs

Status: **proposal, waiting for approval** (24 Sep 2026). Nothing in this plan is implemented yet.

The paper (`main.tex`) now asks one research question: can a single consumer GPU with 8–12 GB of
memory produce exam questions of the same quality as a large server model, and at what cost in
memory, time and energy? This plan lists what has to be built and run to answer it. Every red
`\tbd{}` value in the paper comes from one of the runs below.

## 1. Research questions and hypotheses (as in the paper)

| | Question | Hypothesis | Decided by |
| --- | --- | --- | --- |
| RQ1 | How large is the gap between a small quantised local model and a large server model, both with naive RAG? | H1: the server is better, mainly in grounding and distractors | L7-naive, L14-naive vs S-naive: paired Wilcoxon + Holm |
| RQ2 | Does planning + verification close the gap, and what does it cost? | H2: L7-verify is non-inferior to S-naive (margin δ = 0.05 = half a question per 10-question exam) | One-sided 95 % bootstrap CI of the paired difference > −0.05; gap closure with CI; cost per exam |
| RQ3 | At a fixed memory budget, bigger model or verification? | H3: L7-verify beats L14-naive on the 12 GB card. H4: the gain from verification shrinks as model size grows | Paired Wilcoxon; difference of differences (verify gain) across 3B / 7B / 14B |
| RQ4 | Does the LLM judge agree with teachers? | Judge–teacher ρ ≥ 0.5 on correctness | Krippendorff α, Spearman ρ, Cohen κ |

## 2. Systems to run

| ID | Model tag (Ollama) | Pipeline | GPU tier | Seeds | Existing config |
| --- | --- | --- | --- | --- | --- |
| L7-naive | `qwen2.5:7b` (Q4_K_M) | naive | 8 GB | 3 | E0 (rename) |
| L7-plan | `qwen2.5:7b` | blueprint, no verifier | 8 GB | 1 | E1 |
| L7-verify | `qwen2.5:7b` | blueprint + verifier | 8 GB | 1 | E2 |
| L3-verify | `qwen2.5:3b` | blueprint + verifier | 8 GB | 1 | **new** |
| L8-verify | `llama3.1:8b` | blueprint + verifier | 8 GB | 1 | **new** |
| L7q8-verify | `qwen2.5:7b-instruct-q8_0` | blueprint + verifier | 12 GB | 1 | **new** |
| L14-naive | `qwen2.5:14b` (Q4_K_M) | naive | 12 GB | 3 | **new** |
| L14-verify | `qwen2.5:14b` | blueprint + verifier | 12 GB | 1 | **new** |
| S-naive | server model (see decision D2) | naive | server | 3 | E4 (all 39 docs, not the 12-doc subset) |
| S-verify | server model | blueprint + verifier | server | 1 | E4b (12-doc subset is enough) |

The earlier ablations (hybrid retrieval E2h, concept graph E3, "fast" E2f, chunking E5a–c) stay in the
harness but leave the paper, because they do not answer the consumer-GPU question. They can go into
a follow-up paper or the TDK thesis.

**Why S-naive now runs on all 39 documents:** H2 is the main claim, and a non-inferiority test needs
power. With 39 paired documents and a standard deviation of paired differences σ ≈ 0.10, the power
to show non-inferiority when there is no true difference is about 0.93; at σ ≈ 0.15 it falls to
about 0.67. The smoke run (R0) gives the first estimate of σ; if it is above 0.12 we either add
documents or run two seeds for L7-verify.

## 3. Implementation needed (code, before the runs)

| # | Change | Where | Why | Size |
| --- | --- | --- | --- | --- |
| I1 | **GPU telemetry:** sample `memory.used` and `power.draw` at 2 Hz; per-exam energy (Wh, trapezoid integration); 30 s idle-power baseline at run start; GPU name, total memory and driver version in `run.json` | `mimir_eval/vram.py` → `gpu.py`, `runner.py` | "Wh per exam" and peak memory are core results | S |
| I2 | **Runtime telemetry:** output tokens/s from Ollama's `eval_count / eval_duration`; exclude model load time; call `GET /api/ps` at run start and record whether 100 % of the model is on the GPU (`size_vram == size`), flag the run otherwise | `llm.py`, `runner.py` | Proves the model really ran within the tier's memory, with no CPU offload | S |
| I3 | **Per-stage cost:** time and tokens per stage (planning, writing, grounding check, blind answer, retries), not only calls | `blueprint/pipeline.py` | Table VI in the paper; shows which check to make adaptive | S |
| I4 | **Configs for the new systems** (table above) plus a `tier` field; rename arm labels to the paper's IDs | `configs/` | New arms for RQ3 | S |
| I5 | **Statistics:** non-inferiority test (one-sided bootstrap CI of the paired difference against −δ), gap closure with bootstrap CI, verify gain per model size (difference of differences) with CI | `stats.py`, `report.py` | H2–H4 need these tests; today only two-sided Wilcoxon exists | M |
| I6 | **Paper tables straight from the report:** write `tab_main.tex`, `tab_stages.tex`, `tab_agree.tex` and the data for the quality-vs-memory figure, so the paper `\input`s them instead of copying numbers by hand | `report.py`, `paper/main.tex` | No copy errors; re-running regenerates the paper | M |
| I7 | **Language check:** flag questions not written in the requested language (Hungarian document → Hungarian question) | `schema.py`, `metrics.py` | Small multilingual models often switch to English; this is a Hungarian-specific failure mode | S |
| I8 | **Error-analysis export:** sample of failed questions per system (grounding or blind test failed) into an xlsx with a coding column (key not in source, two correct options, distractor true, answerable without source, wrong language or format) | new `mimir_eval/errors.py`, CLI command | "Error analysis" paragraph | S |
| I9 | **Teacher rating subset:** export for the core systems only (see D4) | `rating.py` (config only) | Keeps the rating load realistic | S |

S = up to half a day, M = one to two days. Everything is tested with the existing mock-LLM
end-to-end tests; GPU telemetry falls back to "not measured" without `nvidia-smi`.

## 4. Runs, in order

| Step | What | Hardware | Rough time |
| --- | --- | --- | --- |
| R0 | Smoke run: every system on 2 documents; measure seconds per call, peak memory, energy; estimate σ for the power check | both GPUs | 2–3 h |
| R1 | Freeze the dataset as `eval-v1`; 8 GB tier: L7-naive, L7-plan, L7-verify, L3-verify, L8-verify | 8 GB card | ~1–1.5 days |
| R2 | 12 GB tier: L7q8-verify, L14-naive, L14-verify; plus L7-verify on 6 documents to time it on the same card | 12 GB card | ~1.5–2 days |
| R3 | Server: S-naive (all documents), S-verify (12 documents) | university server | a few hours |
| R4 | Score everything with the judge | university server | ~1 day |
| R5 | Teacher rating (3 teachers) and error-analysis coding (authors) | people | 1–2 weeks elapsed |
| R6 | `report` → paper tables and figure; write the results text | — | 1–2 days |

Time estimates assume about 6–10 s per short call for the 7B model on an 8 GB card and roughly
twice that for 14B on a 12 GB card; R0 replaces them with measured values. R1 and R2 can run in
parallel on the two machines, and every step resumes after an interruption.

## 5. Decisions needed

| # | Question | Default if no answer |
| --- | --- | --- |
| D1 | Which GPUs can we use for the runs? The roadmap names an RTX 3070 Ti 8 GB and an RTX 3060 12 GB. | Those two |
| D2 | Which server model is the reference? The current E4 config uses `qwen38udq8xl`; we need its real name and size for the paper. | Keep it, document name and size |
| D3 | Keep all five local configurations, or trim (e.g. drop Llama-3.1-8B or the Q8 variant)? | Keep all five |
| D4 | Teacher rating: 3 teachers × 15 questions × 4 core systems (L7-naive, L7-verify, L14-naive, S-naive) = 60 questions each, plus 10 calibration items. | As stated |
| D5 | Target venue and deadline (IEEE-format conferences such as SACI, CINTI or SISY; or AIED / BEA, which use other templates). | IEEE conference format, 6 pages |

## 6. What changed in the paper

- **Research question, not a system description:** the title, abstract, introduction, RQs and hypotheses now centre on consumer GPUs.
- **Removed:** the progress bar and remaining-time estimate, the service architecture, frontend tests, and the GDPR tooling details. GDPR and the AI Act now appear only in a short "Ethical Considerations" section.
- **Added:**
  - an analytical memory budget with a table of what fits 8 and 12 GB;
  - related work on small models for question generation, quantisation, consumer-GPU energy, test-time compute and Hungarian;
  - a hardware and measurement protocol table;
  - a non-inferiority analysis with a pre-specified margin;
  - a per-stage cost table, a judge-agreement table, an error-analysis plan and threats to validity.
- **Length:** about 5.5 pages. The free half page is for the results text once the runs are done.
