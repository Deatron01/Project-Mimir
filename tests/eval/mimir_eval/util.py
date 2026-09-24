"""Small shared helpers: JSON lines, hashing, git info, text normalisation."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Iterator


def read_jsonl(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def iter_jsonl(path: Path) -> Iterator[dict]:
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def append_jsonl(path: Path, record: dict) -> None:
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_jsonl(path: Path, records: Iterable[dict]) -> None:
    with Path(path).open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_json(path: Path, obj: Any) -> None:
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def sha1(*parts: str) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def git_info(repo_dir: Path) -> dict:
    def run(*args: str) -> str:
        try:
            return subprocess.run(["git", *args], cwd=repo_dir, capture_output=True,
                                  text=True, timeout=10).stdout.strip()
        except Exception:
            return ""
    return {"commit": run("rev-parse", "HEAD"),
            "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(run("status", "--porcelain", "--", "services", "tests/eval"))}


_WS = re.compile(r"\s+")


def norm_text(s: str) -> str:
    """Lower-case, strip accents-insensitive punctuation noise, collapse whitespace."""
    s = unicodedata.normalize("NFC", s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return _WS.sub(" ", s).strip()


def token_overlap(needle: str, haystack: str) -> float:
    """Share of the needle's word tokens that appear in the haystack (0..1)."""
    n = norm_text(needle).split()
    if not n:
        return 0.0
    h = set(norm_text(haystack).split())
    return sum(1 for t in n if t in h) / len(n)


def evidence_in(evidence: str, text: str, threshold: float = 0.8) -> bool:
    """True if an evidence sentence is (almost) contained in a chunk of text."""
    if norm_text(evidence) and norm_text(evidence) in norm_text(text):
        return True
    return token_overlap(evidence, text) >= threshold


class Haystack:
    """A text prepared once for many evidence lookups (same rule as evidence_in)."""

    def __init__(self, text: str):
        self.norm = norm_text(text)
        self.tokens = set(self.norm.split())

    def contains(self, evidence: str, threshold: float = 0.8) -> bool:
        ne = norm_text(evidence)
        if ne and ne in self.norm:
            return True
        toks = ne.split()
        return bool(toks) and sum(1 for t in toks if t in self.tokens) / len(toks) >= threshold


def truthy(v) -> bool:
    """LLM JSON sometimes says "true"/"false" as strings; bool("false") would be True."""
    if isinstance(v, str):
        return v.strip().lower() in ("true", "yes", "igen", "1")
    return bool(v)
