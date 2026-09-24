# Conference paper

`main.tex`: "MIMIR: Verifiable, Privacy-Preserving Exam Generation with Local Language Models". An
IEEE conference paper (IEEEtran, two columns, 6 pages) on why a verifiable generation method beats
sending a document to an LLM, how Mimir implements it on a consumer GPU without retaining teaching
material, and how it is evaluated. `main.pdf` is the compiled draft.

**Status:** method, evaluation methodology and pilot results are written from real data. The
main-study results are one red `\tbd{}` placeholder in the Discussion; the runs that produce them are
in [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md) (waiting for approval).

## Build

```bash
latexmk -pdf main.tex        # TeX Live with IEEEtran and pgfplots; or upload the folder to Overleaf
```

## Where each number comes from

| Paper | Source |
| --- | --- |
| Table VI (pilot), Fig. 2 | `tests/eval/report_pilot/pilot/eredmenyek_tabla.csv`, `tests/eval/results_pilot/*/exam_metrics.csv` |
| Table VII (verifier vs judge) | `results_pilot/{E2,E2f,E2h,E3}_*/exams.jsonl` (`verified`) joined with `questions.jsonl` (`grounded`, `blind_correct`, `judge_would_use`) |
| Table VIII (rubric scores) | `results_pilot/*/questions.jsonl` (`judge_*` fields, means over 30 questions) |
| Table IX (examples) | `results_pilot/E0_*` seed 1 q01 and `results_pilot/E3_*` seed 1 q01, translated |
| Leakage rates | Key-in-stem: at least 80 % of the key's word tokens in the stem (`mimir_eval.util.token_overlap`); non-question: the stem does not end in "?" |
| Stem and option lengths | Mean characters of `text` and of all four option texts, `questions.jsonl` |
| Run-to-run noise | E0 and E5a have identical chunks and retrieved context (`exams.jsonl`), indices 0.83 vs 0.90 |
| GPU memory | `vram_baseline_mib` and `vram_peak_mib` in `results_pilot/*/exams.jsonl` |
| Table III (memory budget) | Published model architectures and GGUF file sizes; runtime overhead assumed 0.6 GB (estimate, as the caption says) |
| Table IV (dataset) | `tests/eval/dataset/manifest*.yaml` |
| 68–71 % past the 512-token window | Document lengths at 4.0–4.5 characters per token (estimate) |
| Fallback exams | `tests/Test_Result_20260503_130508/*_Generated.json` |

## Before submission

1. Fill in the GPU model (Section VII), the authors, affiliation, e-mails and the acknowledgment.
2. Run the main study (plan) and replace the red placeholder with its results.
3. Check the venue's template and page limit, and each reference against its published version
   (several are 2026 arXiv preprints).
