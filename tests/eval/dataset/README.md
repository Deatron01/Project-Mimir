# Evaluation dataset

`manifest.yaml` lists every document the harness runs on; imported datasets are pulled in with
`include:`. Target for the TDK paper: 36+ documents in two languages, three length bands, several
subjects, with gold questions and evidence sentences.

| Part | Language | Documents | Source and license | Gold questions |
| --- | --- | --- | --- | --- |
| Pilot (`documents:` below) | HU | 3 short | own texts (`tests/TestDocs`) | 4 per doc, MCQ, evidence added by hand |
| `manifest_eduqg.yaml` | EN | 12 (4 short, 4 medium, 4 long) | [EduQG](https://github.com/hadifar/question-generation): OpenStax textbooks, CC BY 4.0 | 4–10 per doc, expert-written MCQs with evidence sentences, some Bloom labels |
| `manifest_milqa.yaml` | HU | 24 (8 per band) | [MILQA](https://huggingface.co/datasets/SzegedAI/MILQA): Hungarian Wikipedia, CC BY-SA 4.0 | 4–10 per doc, open questions with short answer and long-answer evidence |

Subjects in the EduQG part: life sciences (biology, anatomy, microbiology), humanities (sociology,
psychology, U.S. history, government), law (business law, ethics) and economics (accounting). Each
subject has one short, one medium and one long document, with easy, medium and hard exams.

Rebuild or extend: `python -m mimir_eval import eduqg --n 12 --seed 1` and
`python -m mimir_eval import milqa --n 24 --seed 1` (both rewrite their own manifest file). For MILQA,
set each document's `subject` by hand after import (Wikipedia articles have no subject label), or
pick articles with `--titles "Arany János" "Fotoszintézis" ...`.

Why these two: they are the best fits we found that give, for each question, the source
passage **and** the sentence(s) that prove the answer, which the grounding and retrieval metrics
need. EduQG adds expert distractors (reference for distractor quality) and Bloom labels. MILQA is
the largest Hungarian reading-comprehension set with answer spans. Other options considered: SciQ
(EN, CC BY-NC, short support paragraphs only), RACE (EN exam MCQs, non-commercial), HuRC (HU, cloze
questions on news, no exam-style questions). A parallel HU translation of some EduQG documents (with
the GenAI server, checked by hand) would let the paper compare languages on identical content.

## Adding a document

1. Put the file in `dataset/docs/` (`.txt`, `.md` or text-based `.pdf`; Wellspring does not read `.docx`).
2. Add an entry to `manifest.yaml` (the template is at the bottom of the file).
3. Check that the license allows use. Set `public: false` for anything that must not be released.
4. Run `python -m mimir_eval check configs/e0_naive_local.yaml` to confirm the file loads.

## Gold questions (optional, 12 documents)

Same shape as `tests/TestBaseline/*.json`, plus `evidence`: the sentence(s) of the document that
prove the answer, **copied verbatim**. Evidence makes retrieval recall@k measurable, and it lets us
check whether the generated questions cover the same facts.

```json
{
  "teszt_metaadatok": {"tema": "...", "nehezseg": "kozepes", "nyelv": "hu"},
  "kerdesek": [
    {
      "id": "q_topic_001",
      "bloom_szint": "Megértés",
      "kerdes": "...?",
      "helyes_valasz": "...",
      "disztraktorok": ["...", "...", "..."],
      "magyarazat": "...",
      "evidence": ["Exact sentence from the document."]
    }
  ]
}
```

Rules for writing gold questions: 8–10 per document; mix of Bloom levels that matches the document's
difficulty; no "according to the text" wording; each answer supported by one or two sentences.

## Freezing

Before the first run that goes into the paper, set `version: eval-v1` and commit. Every run
records the dataset version in `run.json`, so results made on different versions are never
mixed by accident.

The pilot gold files in `gold/` are copies of `tests/TestBaseline/*.json` with evidence sentences
added. Three of the twelve pilot questions say "a szöveg alapján"/"a megadott szöveg alapján";
reword them before freezing, or they will count against the meta-reference metric if the gold set
is ever scored as a reference arm.
