# Conference paper

`main.tex`: "MIMIR: Verifiable, Privacy-Preserving Exam Generation with Local Language Models". An
IEEE conference paper (IEEEtran, two columns, 6 pages) on why a verifiable generation method beats
sending a document to an LLM, how Mimir implements it on a consumer GPU without retaining teaching
material, and how it is evaluated. `main.pdf` is the compiled draft.

**Status:** method, evaluation methodology and pilot results are written from real data. The
main-study results are one red `\tbd{}` placeholder in the Discussion; the runs that produce them are
in [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md) (code changes implemented; runs pending).

## Build

```bash
latexmk -pdf main.tex        # TeX Live with IEEEtran and pgfplots; or upload the folder to Overleaf
```

## Generated tables

`tables/` holds tables written by the harness, not by hand. `python -m mimir_eval report` writes them
to `report/<name>/latex/` (with `paper_numbers.json`, every number in them); copy them here:

```bash
cd tests/eval
python -m mimir_eval report --results results_pilot --name pilot --out /tmp/report
cp /tmp/report/pilot/latex/tab_main.tex ../../paper/tables/pilot_main.tex          # Table VI
cp /tmp/report/pilot/latex/tab_verifier.tex ../../paper/tables/pilot_verifier.tex  # Table VII
```

`pilot_verifier_arms.tex` (precision, recall and Cohen's κ of the verifier against the judge, per arm)
and `pilot_leakage.tex` are generated too; the text quotes their ranges. The main study's tables come
out of the same command on `results/`.

## Where each number comes from

| Paper | Source |
| --- | --- |
| Table VI (pilot) | `tables/pilot_main.tex`, generated from `tests/eval/results_pilot/*/exam_metrics.csv` and `questions.jsonl` (leakage) |
| Fig. 2 | the same numbers (`fig_quality_time.dat` in the report's `latex/` folder) |
| Table VII (verifier vs judge) | `tables/pilot_verifier.tex`: `results_pilot/{E2,E2f,E2h,E3}_*/exams.jsonl` (`verified`) joined with `questions.jsonl` (`grounded`, `blind_correct`, `judge_would_use`); blind answer rates exclude questions the judge could not answer, as everywhere else |
| Verifier κ, recall | `tables/pilot_verifier_arms.tex` |
| Table VIII (rubric scores) | `results_pilot/*/questions.jsonl` (`judge_*` fields, means over 30 questions) |
| Table IX (examples) | `results_pilot/E0_*` seed 1 q01 and `results_pilot/E3_*` seed 1 q01, translated |
| Leakage rates | `tables/pilot_leakage.tex`. Key in stem: at least 80 % of the key's word tokens in the stem, for keys of three or more words (`mimir_eval.schema.key_in_stem`); non-question: an MCQ stem that ends in neither "?" nor ":" (`stem_is_question`) |
| Stem and option lengths | Mean characters of `text` and of all four option texts, `questions.jsonl` |
| Run-to-run noise | E0 and E5a have identical chunks and retrieved context (`exams.jsonl`), indices 0.83 vs 0.90 |
| GPU memory | `vram_baseline_mib` and `vram_peak_mib` in `results_pilot/*/exams.jsonl` |
| Table III (memory budget) | Published model architectures and GGUF file sizes; runtime overhead assumed 0.6 GB (estimate, as the caption says) |
| Table IV (dataset) | `tests/eval/dataset/manifest*.yaml` |
| 68–71 % past the 512-token window | Document lengths at 4.0–4.5 characters per token (estimate) |
| Fallback exams | `tests/Test_Result_20260503_130508/*_Generated.json` |

## Before submission

1. Fill in the GPU model (Section VII), the authors, affiliation, e-mails and the acknowledgment.
   New runs record the GPU in `run.json` (`hardware.gpus`).
2. Run the main study (plan) and replace the red placeholder with its results.
3. Check the venue's template and page limit, and each reference against its published version
   (several are 2026 arXiv preprints).
