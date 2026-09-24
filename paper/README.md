# Conference paper

`main.tex` is a 6-page IEEE conference paper (IEEEtran, two columns) about Mimir: system, blueprint
pipeline, privacy design and the TDK evaluation protocol. `main.pdf` is the compiled version.

## Build

```bash
latexmk -pdf main.tex        # needs TeX Live with IEEEtran, pgfplots, algorithms/algorithmicx
```

On Windows, MiKTeX installs the missing packages on first build, or upload the folder to Overleaf.

## Before submission

1. **Run the full evaluation** (ROADMAP AI-19; commands in `tests/eval/README.md`), then fill
   Table VI ("Quality by arm"). Every value there is a red `\tbd{--}` placeholder. Take the values from
   `tests/eval/report/<name>/eredmenyek_tabla.csv`:

   | Table VI column | CSV column |
   | --- | --- |
   | Format | `format_compliant` |
   | Ground. | `grounding_rate` |
   | Blind | `blind_answerability` |
   | Distr. | `distractor_validity` |
   | Index [CI] | `minosegi_index` [`ci_lo`, `ci_hi`] |
   | min/exam | `ido_median_s` / 60 |

   Then add one or two sentences of findings under Table VI, with p-values and effect sizes from
   `szignifikancia.csv`. If the teacher rating is done, cite the agreement numbers from
   `tabla3_egyetertes`. Remove the `\tbd` sentence ("values shown in red are placeholders").
2. **Fill the placeholders**: authors, affiliation and e-mails in `\author`, and the acknowledgment.
3. Check the venue's page limit and template; IEEEtran conference format is used here.

## Where the numbers come from

Only numbers that exist in the repository are used; nothing is estimated from model outputs.

| Paper | Source |
| --- | --- |
| Table III (dataset), Fig. 3 | `tests/eval/dataset/manifest*.yaml` (39 documents, 326 reference questions) |
| 68–71 % of text past the encoder window | Computed from document lengths at 4.0–4.5 characters per token (512 tokens ≈ 2,048–2,304 characters); an estimate, as stated in the text |
| Fallback exams counted as results | `tests/Test_Result_20260503_130508/` (all three `*_Generated.json` are the hard-coded error exam) |
| Table V (latency) | `tests/Test_Result_20260327_125252/e2e_report_20260327_125252.md` |
| Table II (LLM calls per exam) | Derived from the pipeline design (`tests/eval/mimir_eval/blueprint/pipeline.py`), not measured |
| Remaining-time formula | `services/bifrost/jobs.py` |
| Arms, metrics, statistics | `tests/eval/configs/*.yaml`, `tests/eval/mimir_eval/` |
| Test counts (Section VII-D) | `tests/eval/tests_unit` (32), `frontend` Vitest (48) and Playwright (17), as of 24 Sep 2026 |
