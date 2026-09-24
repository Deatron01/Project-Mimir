# Conference paper

`main.tex`: "Do Teachers Need a Data Centre? Verifiable Exam Question Generation with Small Language
Models on Consumer GPUs". An IEEE conference paper (IEEEtran, two columns, 6-page target) on whether
an 8–12 GB consumer GPU can produce exam questions of server-model quality, and at what cost in
memory, time and energy. `main.pdf` is the compiled draft.

**Status:** method and experimental design are written; results are red `\tbd{}` placeholders.
The experiments that produce them are in [`EXPERIMENT_PLAN.md`](EXPERIMENT_PLAN.md), which is
waiting for approval.

## Build

```bash
latexmk -pdf main.tex        # TeX Live with IEEEtran and pgfplots; or upload the folder to Overleaf
```

## Where each number comes from

| Paper | Source |
| --- | --- |
| Table I (memory budget) | Computed from the models' published architectures (layers, key–value heads, head size) and the GGUF file sizes; runtime overhead assumed 0.6 GB. Estimates, as the caption says; measured peaks come from the runs |
| Table II (dataset) | `tests/eval/dataset/manifest*.yaml` (39 documents, 326 reference questions) |
| 68–71 % of text past the 512-token window | Document lengths at 4.0–4.5 characters per token; an estimate |
| Tables III–VII, Fig. 2, all red values | Runs R0–R6 in `EXPERIMENT_PLAN.md`, via `python -m mimir_eval report` |

## Before submission

1. Run the plan, then fill the red values (or `\input` the tables that `report` will write, see plan item I6).
2. Fill in authors, affiliation, e-mails, hardware (Table III), the server model name and the acknowledgment.
3. Check the venue's template and page limit.
4. Check each reference against the published version (several are 2026 arXiv preprints).
