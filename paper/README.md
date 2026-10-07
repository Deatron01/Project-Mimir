# Conference paper

`main.tex`: "MIMIR: Verifiable, Privacy-Preserving Exam Generation with Local Language Models". An
IEEE conference paper (IEEEtran, two columns, 6 pages) on why a verifiable generation method beats
sending a document to an LLM, how Mimir implements it on a consumer GPU without retaining teaching
material, and how it is evaluated. `main.pdf` is the compiled draft.

**Status:** method, evaluation methodology, the pilot and the main study (27–28 Sep 2026: 14 arms, nine
documents, six per arm, 1,670 questions; report in `tests/eval/report_main/main`) are written from real
data. The remaining red `\tbd{}` fields are the teacher ratings and the GPU of the main run. The main
study covers nine of the 39 documents; the full run is the next step in
[`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md).

## Build

```bash
latexmk -pdf main.tex        # TeX Live with IEEEtran and pgfplots; or upload the folder to Overleaf
```

## Generated tables

`tables/` holds tables written by the harness, not by hand. `python -m mimir_eval report` writes them
to `report/<name>/latex/` (with `paper_numbers.json`, every number in them); copy them here:

```bash
cd tests/eval
python -m mimir_eval report --results results --name main --out /tmp/report
cp /tmp/report/main/latex/tab_main.tex ../../paper/tables/main_main.tex                  # Table VI
cp /tmp/report/main/latex/tab_significance.tex ../../paper/tables/main_significance.tex  # Table VII
```

`main_verifier.tex`, `main_verifier_arms.tex` (precision, recall and Cohen's κ of the verifier against
the judge, per arm), `main_leakage.tex`, `main_quality_time.dat` (Fig. 2) and `main_numbers.json` (every
number) are generated too; the text quotes them. The `pilot_*` files are the same tables for the pilot
(`--results results_pilot --name pilot`); the paper now quotes the pilot in the text only.

## Where each number comes from

| Paper | Source |
| --- | --- |
| Table VI (main study) | `tables/main_main.tex`, generated from the main runs' `exam_metrics.csv` and `questions.jsonl`; also `tests/eval/report_main/main/eredmenyek_tabla.csv` |
| Table VII (paired tests) | `tables/main_significance.tex`; unadjusted p in `report_main/main/szignifikancia.csv` |
| Fig. 2 | `tables/main_quality_time.dat` |
| Main-study documents (Setup) | `report_main/main/adatkeszlet.csv` (`kiertekelve`); E4/E4b: `documents` in `configs/e4*_server_*.yaml` |
| Verifier vs judge (89 vs 77 %, κ 0.02–0.22) | `tables/main_verifier.tex`, `tables/main_verifier_arms.tex`; "150 of 174" = Σ precision × passed over the local arms |
| Leakage rates | `tables/main_leakage.tex` (pilot: `tables/pilot_leakage.tex`). Key in stem: at least 80 % of the key's word tokens in the stem, for keys of three or more words (`mimir_eval.schema.key_in_stem`); statement stem: ends in neither "?" nor ":" (`stem_is_question`) |
| Per-language indices (E1, E2, E0, E5a–c, B-doc-S) | `report_main/main/eredmenyek.md`, table 5 |
| E4 vs E2 on the three shared documents (0.93 vs 0.95) | E4: `mean_b` of E4 vs E0 in `main_numbers.json` (`significance`); E2: English column of table 5 |
| "Link to Learning", "access economy" examples | `report_main/main/peldak.md`; character positions in `tests/eval/dataset/docs/eduqg/*.txt` |
| Judge context (24,000 characters) | `max_context_chars` in `mimir_eval/config.py`; `Judge.source_for` |
| Pilot findings (Section VII-A) | `tables/pilot_*.tex`; `results_pilot/{E0,E5a}_*/exams.jsonl` (`retrieved`) for the noise; the leaking example: `results_pilot/E3_*` seed 1 q01 |
| GPU memory | `vram_baseline_mib` and `vram_peak_mib` in `results_pilot/*/exams.jsonl` |
| Table III (memory budget) | Published model architectures and GGUF file sizes; runtime overhead assumed 0.6 GB (estimate, as the caption says) |
| Table IV (dataset) | `tests/eval/dataset/manifest*.yaml` |
| 68–71 % past the 512-token window | Document lengths at 4.0–4.5 characters per token (estimate) |
| Fallback exams | `tests/Test_Result_20260503_130508/*_Generated.json` |

## Before submission

1. Fill in the main run's GPU (Limitations; `run.json`, `hardware.gpus`), the authors, affiliation,
   e-mails and the acknowledgment.
2. Import the teacher ratings (`rate-import`) and replace the red placeholder in the Discussion; ideally
   run the core arms on all 39 documents with identical document sets.
3. Check the venue's template and page limit, and each reference against its published version
   (several are 2026 arXiv preprints).
