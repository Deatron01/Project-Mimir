"""Session-scoped concept graph (GraphRAG-lite): concepts, facts and typed relations per chunk.

Built with one LLM call per batch of consecutive chunks (<= batch_chars characters), merged by
normalised name and, when an embedder is given, by embedding similarity. Lives only in memory
for one exam, like the roadmap's session-scoped graph.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

from ..util import norm_text
from .prompts import GRAPH_SYSTEM, graph_prompt


@dataclass
class Concept:
    key: str
    name: str
    definition: str = ""
    parent: str = ""
    chunks: set = field(default_factory=set)
    facts: list = field(default_factory=list)
    aliases: set = field(default_factory=set)


class ConceptGraph:
    def __init__(self):
        self.concepts: dict[str, Concept] = {}
        self.edges: dict[str, set] = defaultdict(set)
        self.relations: list[tuple[str, str, str]] = []
        self._rel_set: set = set()

    # ---------------------------------------------------------------- build
    @staticmethod
    def key(name: str) -> str:
        return norm_text(name)

    def _resolve(self, name: str) -> str | None:
        k = self.key(name)
        if k in self.concepts:
            return k
        for c in self.concepts.values():
            if k in c.aliases:
                return c.key
        return None

    def add_concept(self, name: str, definition: str = "", parent: str = "", chunks=()) -> str | None:
        k = self.key(name)
        if not k or len(k) > 80:
            return None
        existing = self._resolve(name)
        if existing:
            c = self.concepts[existing]
            c.chunks.update(chunks)
            if definition and len(definition) > len(c.definition):
                c.definition = definition
            if parent and not c.parent:
                c.parent = parent
            return existing
        self.concepts[k] = Concept(key=k, name=name.strip(), definition=definition.strip(), parent=parent.strip(),
                                   chunks=set(chunks), aliases={k})
        return k

    def add_relation(self, a: str, rel: str, b: str) -> None:
        ka, kb = self._resolve(a) or self.add_concept(a), self._resolve(b) or self.add_concept(b)
        if ka and kb and ka != kb and (ka, rel, kb) not in self._rel_set:
            self.edges[ka].add(kb)
            self.edges[kb].add(ka)
            self.relations.append((ka, rel, kb))
            self._rel_set.add((ka, rel, kb))

    def merge_similar(self, embedder, threshold: float = 0.92) -> int:
        """Merge near-duplicate concept names (e.g. inflected forms)."""
        keys = list(self.concepts)
        if len(keys) < 2 or embedder is None:
            return 0
        emb = embedder.encode([self.concepts[k].name for k in keys])
        sim = emb @ emb.T
        merged = 0
        alive = set(keys)
        for i in range(len(keys)):
            if keys[i] not in alive:
                continue
            for j in range(i + 1, len(keys)):
                if keys[j] in alive and sim[i, j] >= threshold:
                    self._merge(keys[i], keys[j])
                    alive.discard(keys[j])
                    merged += 1
        return merged

    def _merge(self, keep: str, drop: str) -> None:
        a, b = self.concepts[keep], self.concepts.pop(drop)
        a.chunks |= b.chunks
        a.facts += b.facts
        a.aliases |= b.aliases
        if not a.definition:
            a.definition = b.definition
        for n in self.edges.pop(drop, set()):
            self.edges[n].discard(drop)
            if n != keep:
                self.edges[keep].add(n)
                self.edges[n].add(keep)

    # ---------------------------------------------------------------- queries
    def centrality(self, k: str) -> float:
        c = self.concepts[k]
        return len(self.edges.get(k, ())) + 0.5 * len(c.chunks) + 0.5 * len(c.facts)

    def siblings(self, k: str, limit: int = 6) -> list[Concept]:
        """Concepts with the same parent, or linked to the same neighbour: good distractor sources."""
        c = self.concepts[k]
        pk = self.key(c.parent) if c.parent else ""
        out = []
        for other in self.concepts.values():
            if other.key == k:
                continue
            same_parent = pk and self.key(other.parent) == pk
            shared = bool(self.edges.get(k, set()) & self.edges.get(other.key, set()))
            is_parent_of_sibling = pk and other.key == pk
            if (same_parent or shared) and not is_parent_of_sibling and other.key not in self.edges.get(k, set()):
                out.append(other)
        out.sort(key=lambda o: -self.centrality(o.key))
        return out[:limit]

    def neighbour_chunks(self, k: str) -> list[int]:
        chunks: dict[int, int] = defaultdict(int)
        for n in self.edges.get(k, ()):
            for ch in self.concepts[n].chunks:
                chunks[ch] += 1
        own = self.concepts[k].chunks
        return [c for c, _ in sorted(chunks.items(), key=lambda x: -x[1]) if c not in own]

    def stats(self) -> dict:
        return {"concepts": len(self.concepts), "relations": len(self.relations),
                "facts": sum(len(c.facts) for c in self.concepts.values())}


_CID = re.compile(r"C(\d+)")


def _ids(values, n_chunks: int, default: list[int]) -> list[int]:
    out = []
    for v in values or []:
        m = _CID.search(str(v))
        if m and int(m.group(1)) < n_chunks:
            out.append(int(m.group(1)))
    return out or default


def chunk_batches(chunks: list[str], batch_chars: int) -> list[list[int]]:
    batches, cur, size = [], [], 0
    for i, c in enumerate(chunks):
        if cur and size + len(c) > batch_chars:
            batches.append(cur)
            cur, size = [], 0
        cur.append(i)
        size += len(c)
    if cur:
        batches.append(cur)
    return batches


def build_graph(chunks: list[str], ask, language: str, batch_chars: int = 3000, embedder=None) -> ConceptGraph:
    """ask(system, user) -> dict. One call per batch of chunks."""
    g = ConceptGraph()
    for batch in chunk_batches(chunks, batch_chars):
        block = "\n\n".join(f"[C{i}] {chunks[i]}" for i in batch)
        data = ask(GRAPH_SYSTEM, graph_prompt(block, language)) or {}
        for c in data.get("concepts") or []:
            if isinstance(c, dict) and c.get("name"):
                g.add_concept(str(c["name"]), str(c.get("definition", "")), str(c.get("parent", "")),
                              _ids(c.get("chunk_ids"), len(chunks), batch))
        for f in data.get("facts") or []:
            if not isinstance(f, dict) or not f.get("text"):
                continue
            cid = _ids([f.get("chunk_id")], len(chunks), batch[:1])[0]
            for name in f.get("concepts") or []:
                k = g._resolve(str(name)) or g.add_concept(str(name), chunks=[cid])
                if k:
                    g.concepts[k].facts.append(str(f["text"]))
                    g.concepts[k].chunks.add(cid)
        for r in data.get("relations") or []:
            if isinstance(r, dict) and r.get("source") and r.get("target"):
                g.add_relation(str(r["source"]), str(r.get("relation", "related_to")), str(r["target"]))
        # parents become nodes too, so siblings share a neighbour
        for c in list(g.concepts.values()):
            if c.parent and g.key(c.parent) != c.key:
                g.add_relation(c.name, "is_a", c.parent)
    g.merge_similar(embedder)
    return g


def rank_concepts(g: ConceptGraph, n_chunks: int) -> list[dict]:
    """Planner input from the graph: concepts by centrality, with chunk coverage."""
    out = []
    for k, c in g.concepts.items():
        if not c.chunks:
            continue
        cent = g.centrality(k)
        out.append({"concept": c.name, "description": c.definition or (c.facts[0] if c.facts else ""),
                    "chunk_ids": sorted(c.chunks), "importance": 3 if cent >= 4 else 2 if cent >= 2 else 1,
                    "key": k, "score": cent})
    out.sort(key=lambda x: -x["score"])
    return out


__all__ = ["ConceptGraph", "build_graph", "rank_concepts", "chunk_batches", "np"]
