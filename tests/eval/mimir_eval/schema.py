"""Normalise generated exams and gold files into one question shape, and check format.

Normalised question:
    {"qid", "type", "text", "options": [{"text", "correct"}], "key", "distractors",
     "bloom", "citations"}
"""
from __future__ import annotations

import json
import re

ERROR_MARKERS = ("Generálási Hiba", "túlterheltek", "Generation error")

TYPE_ALIASES = {
    "mcq": "mcq", "multiple_choice": "mcq", "feleletvalasztos": "mcq", "feleletválasztós": "mcq",
    "tf": "tf", "true_false": "tf", "igaz_hamis": "tf", "igaz-hamis": "tf",
    "open": "open", "essay": "open", "kifejtos": "open", "kifejtős": "open",
}
EXPECTED_OPTIONS = {"mcq": 4, "tf": 2}


def parse_llm_json(text: str) -> dict:
    """Same tolerant cleaning Bifrost applies: strip fences, take outermost {...}."""
    cleaned = (text or "").replace("```json", "").replace("```", "").strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)


def is_error_fallback(raw: dict | None) -> bool:
    if not isinstance(raw, dict):
        return False
    blob = json.dumps(raw, ensure_ascii=False)[:2000]
    return any(m in blob for m in ERROR_MARKERS)


def _qtype(q: dict) -> str:
    t = str(q.get("type", "mcq")).strip().lower()
    return TYPE_ALIASES.get(t, t)


def normalize_exam(raw: dict | None) -> list[dict]:
    """Bifrost v1 shape: {"questions": [{"type", "text", "answers": [{"text", "is_correct"}]}]}."""
    if not isinstance(raw, dict):
        return []
    items = raw.get("questions") or raw.get("kerdesek") or []
    out = []
    for i, q in enumerate(items):
        if not isinstance(q, dict):
            continue
        if "answers" in q or "options" in q:
            opts = [{"text": str(a.get("text", "")).strip(),
                     "correct": bool(a.get("is_correct", a.get("correct", False)))}
                    for a in (q.get("answers") or q.get("options") or []) if isinstance(a, dict)]
        else:  # gold-like shape inside a generated exam
            opts = _gold_options(q)
        key = next((o["text"] for o in opts if o["correct"]), "")
        out.append({
            "qid": str(q.get("id") or f"q{i + 1:02d}"),
            "type": _qtype(q),
            "text": str(q.get("text") or q.get("question") or q.get("kerdes") or "").strip(),
            "options": opts,
            "key": key,
            "distractors": [o["text"] for o in opts if not o["correct"]],
            "bloom": q.get("bloom") or q.get("bloom_level") or q.get("bloom_szint"),
            "citations": q.get("citations") or q.get("source_chunks") or [],
            "context_ids": q.get("context_ids") or [],
            "verified": q.get("verified"),
            "planned_concept": q.get("planned_concept"),
        })
    return out


def _gold_options(q: dict) -> list[dict]:
    key = q.get("helyes_valasz") or q.get("answer") or q.get("key") or ""
    dis = q.get("disztraktorok") or q.get("distractors") or []
    return [{"text": str(key), "correct": True}] + [{"text": str(d), "correct": False} for d in dis]


def normalize_gold(raw: dict) -> list[dict]:
    """Gold files: the existing *Base.json shape (kerdesek/kerdes/helyes_valasz/disztraktorok)
    plus an optional "evidence" (or "bizonyitek") list of source sentences per question."""
    items = raw.get("kerdesek") or raw.get("questions") or []
    out = []
    for i, q in enumerate(items):
        ev = q.get("evidence") or q.get("bizonyitek") or []
        if isinstance(ev, str):
            ev = [ev]
        opts = _gold_options(q) if ("helyes_valasz" in q or "answer" in q or "key" in q) else \
            [{"text": a.get("text", ""), "correct": bool(a.get("is_correct"))} for a in q.get("answers", [])]
        out.append({
            "qid": str(q.get("id") or f"g{i + 1:02d}"),
            "type": _qtype(q) if q.get("type") else ("mcq" if len(opts) > 2 else "tf" if len(opts) == 2 else "open"),
            "text": str(q.get("kerdes") or q.get("question") or q.get("text") or ""),
            "key": next((o["text"] for o in opts if o["correct"]), ""),
            "distractors": [o["text"] for o in opts if not o["correct"]],
            "bloom": q.get("bloom_szint") or q.get("bloom"),
            "explanation": q.get("magyarazat") or q.get("explanation") or "",
            "evidence": [str(e) for e in ev],
        })
    return out


def question_shape_ok(q: dict) -> bool:
    if not q["text"]:
        return False
    correct = sum(1 for o in q["options"] if o["correct"])
    if q["type"] in EXPECTED_OPTIONS:
        return (len(q["options"]) == EXPECTED_OPTIONS[q["type"]] and correct == 1
                and all(o["text"] for o in q["options"]))
    if q["type"] == "open":
        return correct >= 1 and bool(q["key"])
    return False


def exam_format(questions: list[dict], n_requested: int, types: list[str]) -> dict:
    n = len(questions)
    shape = [question_shape_ok(q) for q in questions]
    type_ok = [q["type"] in types for q in questions]
    return {
        "n_generated": n,
        "n_requested": n_requested,
        "count_ok": n == n_requested,
        "shape_ok_rate": (sum(shape) / n) if n else 0.0,
        "type_ok_rate": (sum(type_ok) / n) if n else 0.0,
        "format_compliant": bool(n == n_requested and all(shape) and all(type_ok)),
    }


META_PATTERNS = [
    r"\ba (fenti |megadott |fenti )?sz[öo]veg(ben|b[őo]l|re|et)?\b", r"\bsz[öo]veg szerint\b",
    r"\bdokumentum(ban|b[óo]l|ot)?\b", r"\bkontextus(ban|b[óo]l)?\b", r"\bfejezet(ben)?\b",
    r"\bbekezd[ée]s(ben)?\b", r"\bchunk\b", r"\baccording to the (text|document|passage)\b",
    r"\bin the (text|document|passage|context)\b", r"\bthe (above|given) (text|passage)\b",
    r"\b\d+(\.\d+)+\.? ?(pont|section|fejezet)\b",
]
_META_RE = re.compile("|".join(META_PATTERNS), re.IGNORECASE)


def has_meta_reference(text: str) -> bool:
    return bool(_META_RE.search(text or ""))
