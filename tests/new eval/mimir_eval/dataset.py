"""Evaluation dataset: a YAML manifest of documents with optional gold questions."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .config import resolve
from .schema import normalize_gold


@dataclass
class Document:
    id: str
    path: Path
    language: str = "hu"
    subject: str = ""
    difficulty: str = "medium"
    license: str = ""
    public: bool = False
    gold_path: Path | None = None
    extra: dict = field(default_factory=dict)

    @property
    def extension(self) -> str:
        return self.path.suffix.lstrip(".").lower() or "txt"

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()

    def read_text(self) -> str:
        """Plain text for txt/md; binary formats go through Wellspring instead."""
        return self.path.read_text(encoding="utf-8")

    def gold(self) -> list[dict]:
        if not self.gold_path or not self.gold_path.exists():
            return []
        return normalize_gold(json.loads(self.gold_path.read_text(encoding="utf-8")))


@dataclass
class Dataset:
    version: str
    documents: list[Document]
    manifest_path: Path

    def select(self, ids: str | list[str]) -> list[Document]:
        if ids in (None, "all"):
            return list(self.documents)
        wanted = list(ids)
        by_id = {d.id: d for d in self.documents}
        missing = [i for i in wanted if i not in by_id]
        if missing:
            raise KeyError(f"documents not in manifest: {missing}")
        return [by_id[i] for i in wanted]


def load_dataset(manifest: str | Path) -> Dataset:
    manifest = resolve(manifest)
    raw = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    base = manifest.parent
    docs = []
    seen = set()
    entries = [(d, base) for d in raw.get("documents") or []]
    for inc in raw.get("include") or []:  # e.g. manifest_eduqg.yaml written by an importer
        inc_path = resolve(inc, base)
        if not inc_path.exists():
            print(f"[dataset] note: {inc_path.name} not found (run `python -m mimir_eval import ...`); skipped")
            continue
        inc_raw = yaml.safe_load(inc_path.read_text(encoding="utf-8")) or {}
        entries += [(d, inc_path.parent) for d in inc_raw.get("documents") or []]
    for d, base in entries:
        if d["id"] in seen:
            raise ValueError(f"duplicate document id {d['id']}")
        seen.add(d["id"])
        path = resolve(d["path"], base)
        if not path.exists():
            raise FileNotFoundError(f"{d['id']}: {path}")
        known = {"id", "path", "language", "subject", "difficulty", "license", "public", "gold"}
        docs.append(Document(
            id=d["id"], path=path,
            language=d.get("language", "hu"), subject=d.get("subject", ""),
            difficulty=d.get("difficulty", "medium"), license=d.get("license", ""),
            public=bool(d.get("public", False)),
            gold_path=resolve(d["gold"], base) if d.get("gold") else None,
            extra={k: v for k, v in d.items() if k not in known},
        ))
    return Dataset(version=str(raw.get("version", "unversioned")), documents=docs, manifest_path=manifest)
