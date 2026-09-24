"""LLM judge: two calls per question.

1. review  (sees the key): is the key supported by the source, is each distractor wrong and
   on topic, and 1-5 scores on the shared rubric.
2. blind   (does NOT see the key): answer the question from the source; correct if it picks
   the keyed option. Skipped for open questions.

Results are cached on disk by a hash of (judge model, prompt version, prompt), so re-scoring
a run only pays for new questions.
"""
from __future__ import annotations

import json
import random
import threading
from pathlib import Path

from .llm import LLMClient, LLMError
from .rubric import CRITERIA, RUBRIC_EN
from .schema import parse_llm_json
from .util import append_jsonl, read_jsonl, sha1, truthy

JUDGE_PROMPT_VERSION = "judge-v1"
LETTERS = "ABCDEFGH"

SYSTEM = ("You are a strict, careful exam reviewer. The material may be in Hungarian or English; "
          "judge it in its own language. Reply with one valid JSON object only.")


def _rubric_block() -> str:
    return "\n".join(f"- {c}: {RUBRIC_EN[c]}" for c in CRITERIA)


def review_prompt(source: str, q: dict, difficulty: str) -> str:
    opts = "\n".join(f"{LETTERS[i]}. {o['text']}{'   <-- marked correct' if o['correct'] else ''}"
                     for i, o in enumerate(q["options"]))
    wrong = [LETTERS[i] for i, o in enumerate(q["options"]) if not o["correct"]]
    return f"""SOURCE MATERIAL:
\"\"\"
{source}
\"\"\"

EXAM QUESTION (type: {q['type']}, requested difficulty: {difficulty}):
{q['text']}
{opts}

Tasks:
1. key_supported: does the SOURCE support the marked-correct answer? true only if a reader of the source
   would agree it is correct. Quote the supporting sentence in key_evidence (empty if none).
2. For each wrong option {wrong}: is_wrong (the source makes it false or clearly unsupported) and
   on_topic (same subject, plausible to a student).
3. Score 1-5 on this rubric (distractor_quality null for open questions):
{_rubric_block()}
4. bloom_level: one of remember, understand, apply, analyze, evaluate, create.
5. would_use: true/false.

JSON shape:
{{"key_supported": true, "key_evidence": "...", "distractors": [{{"option": "B", "is_wrong": true, "on_topic": true}}],
 "scores": {{"correctness": 5, "clarity": 4, "distractor_quality": 3, "bloom_fit": 4}},
 "bloom_level": "understand", "would_use": true, "rationale": "one or two sentences"}}"""


def blind_prompt(source: str, q: dict, order: list[int]) -> str:
    opts = "\n".join(f"{LETTERS[j]}. {q['options'][i]['text']}" for j, i in enumerate(order))
    return f"""SOURCE MATERIAL:
\"\"\"
{source}
\"\"\"

Answer this exam question using only the source. Exactly one option is intended to be correct.
{q['text']}
{opts}

JSON shape: {{"answer": "A", "confidence": 0.9}}"""


class Judge:
    def __init__(self, cfg: dict, cache_path: Path):
        self.cfg = cfg
        self.llm = LLMClient.from_config(cfg)
        self.cache_path = cache_path
        self.cache = {r["key"]: r["value"] for r in read_jsonl(cache_path)}
        self.calls = 0
        self._lock = threading.Lock()   # judge_question is called from several threads

    def describe(self) -> dict:
        return {**self.llm.describe(), "prompt_version": JUDGE_PROMPT_VERSION}

    def _ask(self, kind: str, prompt: str) -> dict:
        key = sha1(self.llm.provider, self.llm.model, JUDGE_PROMPT_VERSION, kind, prompt)
        if key in self.cache:
            return self.cache[key]
        value: dict = {"_error": "not run"}
        for _ in range(2):  # one retry for unparsable output
            try:
                res = self.llm.chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
                                    json_mode=True, seed=0)
                with self._lock:
                    self.calls += 1
                value = parse_llm_json(res.text)
                if not isinstance(value, dict):
                    raise ValueError("judge returned non-object JSON")
                break
            except (LLMError, ValueError, json.JSONDecodeError) as e:
                value = {"_error": str(e)[:300]}
        if "_error" not in value:
            with self._lock:
                self.cache[key] = value
                append_jsonl(self.cache_path, {"key": key, "value": value})
        return value

    def source_for(self, exam: dict, q: dict | None = None) -> tuple[str, str]:
        """Full document when it fits; else the chunks this question was written from; else the
        retrieved context the generator saw."""
        doc = exam.get("doc_text") or ""
        lim = self.cfg["max_context_chars"]
        if doc and len(doc) <= lim:
            return doc, "document"
        chunks = exam.get("chunks") or []
        ids = [i for i in ((q or {}).get("context_ids") or []) if isinstance(i, int) and 0 <= i < len(chunks)]
        if ids:
            return "\n\n".join(chunks[i] for i in ids)[:lim], "question_context"
        return exam.get("context_text", "")[:lim], "retrieved_context"

    def judge_question(self, exam: dict, q: dict) -> dict:
        source, source_kind = self.source_for(exam, q)
        out: dict = {"judge_source": source_kind}
        rv = self._ask("review", review_prompt(source, q, exam.get("difficulty", "")))
        if "_error" in rv:
            out["judge_error"] = rv["_error"]
        else:
            scores = rv.get("scores") or {}
            for c in CRITERIA:
                v = scores.get(c)
                out[f"judge_{c}"] = _clip15(v)
            if q["type"] == "open":
                out["judge_distractor_quality"] = None
            out["grounded"] = truthy(rv.get("key_supported"))
            out["key_evidence"] = rv.get("key_evidence", "")
            ds = [d for d in (rv.get("distractors") or []) if isinstance(d, dict)]
            if q["distractors"] and ds:
                out["distractor_valid_rate"] = sum(1 for d in ds if truthy(d.get("is_wrong")) and truthy(d.get("on_topic"))) / len(ds)
                out["distractor_wrong_rate"] = sum(1 for d in ds if truthy(d.get("is_wrong"))) / len(ds)
            out["judge_bloom_level"] = rv.get("bloom_level")
            out["judge_would_use"] = truthy(rv.get("would_use")) if rv.get("would_use") is not None else None
            out["judge_rationale"] = rv.get("rationale", "")
        if q["type"] != "open" and len(q["options"]) >= 2:
            order = list(range(len(q["options"])))
            random.Random(sha1(q["text"])).shuffle(order)
            bl = self._ask("blind", blind_prompt(source, q, order))
            ans = str(bl.get("answer", "")).strip().upper()[:1]
            if "_error" in bl or ans not in LETTERS[: len(order)]:
                out["blind_correct"] = None
            else:
                out["blind_correct"] = bool(q["options"][order[LETTERS.index(ans)]]["correct"])
        return out


def _clip15(v) -> int | None:
    try:
        return max(1, min(5, int(round(float(v)))))
    except (TypeError, ValueError):
        return None
