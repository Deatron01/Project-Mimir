"""Blueprint pipeline (ROADMAP section 5): plan -> retrieve per slot -> generate one question ->
verify -> assemble. Arms E1-E3 switch parts on and off through `pipeline:` config keys:

    verifier: false|true    E1 = false; E2/E3 = true (schema, meta-reference, citations,
                            grounding + distractor check, blind answer test; retries with feedback)
    blind_test: true        "Fast" mode = false (skips the blind answer call)
    max_retries: 1          per slot, then one replacement concept, then keep best attempt (flagged)
    graph: false|true       E3: concept graph as planner input, graph distractors, 1-hop chunks
    retrieval: dense|hybrid dense = Bifrost /search; hybrid = BM25 + dense with RRF
    retrieval_k: 3
    spare_concepts: 3       extra planned concepts used as replacements
    dedupe_threshold: 0.9   embedding similarity above which a question counts as a duplicate
    embedder: e5            for dedupe and concept merging ("bow" in tests)
"""
from __future__ import annotations

import random
import time

import numpy as np

from ..embed import get_embedder
from ..pipelines import BasePipeline, PreparedDoc, ExamSpec
from ..schema import has_meta_reference, normalize_exam, parse_llm_json, question_shape_ok
from ..util import truthy
from .graph import ConceptGraph, build_graph, rank_concepts
from .prompts import (BP_PROMPT_VERSION, GENERATOR_SYSTEM, PLANNER_SYSTEM, VERIFIER_SYSTEM, blind_prompt,
                      generator_prompt, grounding_prompt, planner_prompt)
from .retrieval import BM25, rrf

BLOOM_ORDER = ["remember", "understand", "apply", "analyze", "evaluate"]
BLOOM_MIX = {
    "easy": {"remember": 0.5, "understand": 0.5},
    "medium": {"understand": 0.4, "apply": 0.4, "analyze": 0.2},
    "hard": {"apply": 0.3, "analyze": 0.4, "evaluate": 0.3},
}
DEFAULTS = {"verifier": False, "blind_test": True, "max_retries": 1, "graph": False, "retrieval": "dense",
            "retrieval_k": 3, "spare_concepts": 3, "dedupe_threshold": 0.9, "embedder": "e5",
            "overview_chars": 12000, "graph_batch_chars": 3000, "max_context_chars": 6000}
LETTERS = "ABCDEFGH"


def bloom_plan(n: int, difficulty: str, rng: random.Random) -> list[str]:
    """Largest-remainder allocation of Bloom levels, shuffled, then sorted easy -> hard."""
    mix = BLOOM_MIX.get(difficulty, BLOOM_MIX["medium"])
    raw = {k: v * n for k, v in mix.items()}
    counts = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: -(raw[k] - counts[k]))[: n - sum(counts.values())]:
        counts[k] += 1
    levels = [k for k, c in counts.items() for _ in range(c)]
    rng.shuffle(levels)
    return levels


def allocate_slots(concepts: list[dict], n: int, types: list[str], blooms: list[str]) -> tuple[list[dict], list[dict]]:
    """Greedy coverage: prefer concepts that touch a chunk no slot covers yet, then importance."""
    pool = sorted(concepts, key=lambda c: -int(c.get("importance", 1)))
    chosen, covered = [], set()
    while pool and len(chosen) < n:
        best = max(pool, key=lambda c: (len(set(c["chunk_ids"]) - covered) > 0, int(c.get("importance", 1))))
        pool.remove(best)
        chosen.append(best)
        covered |= set(best["chunk_ids"])
    i = 0
    while len(chosen) < n and concepts:   # fewer concepts than slots: reuse at another Bloom level
        chosen.append({**concepts[i % len(concepts)], "reused": True})
        i += 1
    slots = [{**c, "slot": s, "type": types[s % len(types)], "bloom": blooms[s]} for s, c in enumerate(chosen)]
    return slots, pool


class BlueprintPipeline(BasePipeline):
    kind = "blueprint"
    implemented = True

    def __init__(self, cfg, services, llm):
        super().__init__(cfg, services, llm)
        self.p = {**DEFAULTS, **cfg["pipeline"]}
        self.embedder = get_embedder(self.p["embedder"])

    # ---------------------------------------------------------------- LLM helper
    def _ask(self, system: str, user: str, stage: str, seed: int, attempt: int = 0) -> dict | None:
        for k in range(2):  # one retry for unparsable JSON, with a different seed
            try:
                res = self.llm.chat([{"role": "system", "content": system}, {"role": "user", "content": user}],
                                    json_mode=True, seed=seed * 1000 + attempt * 10 + k)
            except Exception as e:  # network / server error: count and give up on this call
                self.stats["llm_errors"] += 1
                self.stats["last_error"] = str(e)[:200]
                return None
            self.stats["calls"][stage] = self.stats["calls"].get(stage, 0) + 1
            self.stats["tokens"] += (res.prompt_tokens or 0) + (res.completion_tokens or 0)
            self.stats["llm_s"] += res.latency_s
            try:
                data = parse_llm_json(res.text)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
            self.stats["parse_failures"] += 1
        return None

    # ---------------------------------------------------------------- retrieval
    def _search(self, prep: PreparedDoc, query: str, k: int) -> list[int]:
        if self.p["retrieval"] == "hybrid":
            hits, _ = self.services.search(query, len(prep.chunks))
            dense = [i for i in (self._chunk_index(prep, h["payload"].get("text", "")) for h in hits) if i is not None]
            return rrf([dense, self._bm25.ranking(query)])[:k]
        hits, _ = self.services.search(query, k)
        return [i for i in (self._chunk_index(prep, h["payload"].get("text", "")) for h in hits) if i is not None]

    def _slot_context(self, prep: PreparedDoc, slot: dict, extra_k: int = 0) -> list[int]:
        q = f"{slot['concept']}: {slot.get('description', '')}"
        ids = list(dict.fromkeys([i for i in slot.get("chunk_ids", []) if i < len(prep.chunks)][:2]
                                 + self._search(prep, q, self.p["retrieval_k"] + extra_k)))
        if self.graph is not None and slot.get("key") in self.graph.concepts:
            ids += [c for c in self.graph.neighbour_chunks(slot["key"])[:2] if c not in ids]
        out, size = [], 0
        for i in ids:  # keep the context inside the small model's comfort zone
            if out and size + len(prep.chunks[i]["content"]) > self.p["max_context_chars"]:
                break
            out.append(i)
            size += len(prep.chunks[i]["content"])
        return out

    # ---------------------------------------------------------------- planning
    def _overview(self, prep: PreparedDoc) -> str:
        n = len(prep.chunks)
        per = max(120, self.p["overview_chars"] // max(1, n))
        lines = []
        for i, c in enumerate(prep.chunks):
            t = " ".join(c["content"].split())
            lines.append(f"[C{i}] {t[:per]}{'…' if len(t) > per else ''}")
        return "\n".join(lines)

    def _plan(self, prep: PreparedDoc, spec: ExamSpec, seed: int) -> list[dict]:
        n_concepts = spec.n_questions + self.p["spare_concepts"]
        if self.graph is not None:
            return rank_concepts(self.graph, len(prep.chunks))[: n_concepts * 2]
        data = self._ask(PLANNER_SYSTEM, planner_prompt(self._overview(prep), n_concepts, spec.language),
                         "planner", seed) or {}
        concepts = []
        for c in data.get("concepts") or []:
            if not isinstance(c, dict) or not c.get("concept"):
                continue
            ids = []
            for v in c.get("chunk_ids") or []:
                s = str(v).strip().upper().lstrip("C")
                if s.isdigit() and int(s) < len(prep.chunks):
                    ids.append(int(s))
            try:
                imp = int(c.get("importance", 2))
            except (TypeError, ValueError):
                imp = 2
            concepts.append({"concept": str(c["concept"]), "description": str(c.get("description", "")),
                             "chunk_ids": ids, "importance": imp})
        if not concepts:  # planner failed: fall back to one pseudo-concept per chunk
            self.stats["planner_fallback"] = True
            concepts = [{"concept": " ".join(c["content"].split()[:8]), "description": "",
                         "chunk_ids": [i], "importance": 2} for i, c in enumerate(prep.chunks)]
        return concepts

    # ---------------------------------------------------------------- verification
    def _verify(self, q: dict, ctx_ids: list[int], prep: PreparedDoc, seed: int, attempt: int) -> list[str]:
        """Cheapest first. Returns a list of problems (empty = passed)."""
        problems = []
        if not question_shape_ok(q):
            problems.append("A válaszok száma vagy formája nem felel meg a kérdéstípusnak "
                            "(mcq: 4 válasz, 1 helyes; tf: 2 válasz, 1 helyes; open: 1 helyes kulcs).")
        if has_meta_reference(q["text"]):
            problems.append("A kérdés a szövegre/dokumentumra hivatkozik; fogalmazd meg általános vizsgakérdésként.")
        if not self.p["verifier"]:
            return problems
        cited = [i for i in q.get("_cited", []) if i in ctx_ids]
        if not cited:
            problems.append("Adj meg a 'citations' mezőben legalább egy, a kontextusban szereplő azonosítót (pl. C3).")
            cited = ctx_ids
        if problems:
            return problems  # do not pay for LLM checks on a malformed question
        source = "\n\n".join(prep.chunks[i]["content"] for i in cited)
        g = self._ask(VERIFIER_SYSTEM, grounding_prompt(q, source), "verify_grounding", seed, attempt)
        if g is None:
            self.stats["verifier_skipped"] += 1
            return []  # verifier unavailable: do not block the exam, but it is counted
        if not truthy(g.get("key_supported", False)):
            problems.append("A megjelölt helyes választ a hivatkozott részlet nem igazolja. "
                            + str(g.get("problems", "")))
        wrong = g.get("options_wrong") or []
        if q["type"] == "mcq" and wrong and not all(truthy(w) for w in wrong):
            problems.append("Legalább egy disztraktor a forrás szerint nem egyértelműen hibás (lehet, hogy igaz). "
                            + str(g.get("problems", "")))
        if truthy(g.get("ambiguous", False)):
            problems.append("A kérdés kétértelmű, több válasz is védhető.")
        if problems or not self.p["blind_test"] or q["type"] == "open":
            return problems
        order = list(range(len(q["options"])))
        random.Random(seed * 7 + attempt).shuffle(order)
        b = self._ask(VERIFIER_SYSTEM, blind_prompt(q, order, source), "verify_blind", seed, attempt)
        ans = str((b or {}).get("answer", "")).strip().upper()[:1]
        if b is not None and ans in LETTERS[: len(order)] and not q["options"][order[LETTERS.index(ans)]]["correct"]:
            problems.append("Egy független megoldó a forrás alapján más választ jelölt meg helyesnek; "
                            "tedd egyértelműbbé a kérdést vagy a helyes választ.")
        return problems

    def _duplicate_of(self, q: dict, accepted: list[dict]) -> str | None:
        if not accepted:
            return None
        e = self.embedder.encode([q["text"]] + [a["text"] for a in accepted])
        sim = e[1:] @ e[0]
        j = int(np.argmax(sim))
        return accepted[j]["text"] if sim[j] >= self.p["dedupe_threshold"] else None

    # ---------------------------------------------------------------- one slot
    def _fill_slot(self, prep, spec, slot, accepted, seed) -> tuple[dict | None, dict]:
        log = {"slot": slot["slot"], "concept": slot["concept"], "bloom": slot["bloom"], "attempts": []}
        best, best_n = None, (2, 99)   # (malformed?, number of problems): a well-formed question always wins
        feedback, extra_k = None, 0
        for attempt in range(self.p["max_retries"] + 1):
            ctx_ids = self._slot_context(prep, slot, extra_k)
            hints = []
            if self.graph is not None and slot.get("key") in self.graph.concepts:
                hints = [f"{s.name}: {s.definition}".strip(": ") for s in self.graph.siblings(slot["key"])]
            prompt = generator_prompt(slot, [(f"C{i}", prep.chunks[i]["content"]) for i in ctx_ids],
                                      spec.difficulty, spec.language, [a["text"] for a in accepted], hints, feedback)
            raw = self._ask(GENERATOR_SYSTEM, prompt, "generate", seed, attempt + 10 * slot["slot"])
            qs = normalize_exam({"questions": [raw]}) if raw else []
            if not qs:
                log["attempts"].append({"problems": ["unparsable"]})
                feedback = "A válasz nem volt érvényes JSON a megadott formában."
                continue
            q = qs[0]
            q["_raw"] = raw
            q["_cited"] = [int(str(c).upper().lstrip("C")) for c in (raw.get("citations") or [])
                           if str(c).upper().lstrip("C").isdigit()]
            q["_ctx"] = ctx_ids
            problems = self._verify(q, ctx_ids, prep, seed, attempt)
            dup = self._duplicate_of(q, accepted)
            if dup:
                problems.append(f"Túl hasonló egy már elkészült kérdéshez: „{dup}”. Kérdezz a fogalom más oldaláról.")
            log["attempts"].append({"problems": problems})
            if not problems:
                return q, {**log, "passed": True}
            rank = (0 if question_shape_ok(q) else 1, len(problems))
            if rank < best_n:
                best, best_n = q, rank
            if not self.p["verifier"] and not dup and question_shape_ok(q):
                return q, {**log, "passed": True}   # E1: no verification loop, only dedupe/shape
            feedback = "\n".join(f"- {p}" for p in problems)
            if any("nem igazolja" in p for p in problems):
                extra_k += 2   # loop back to retrieval with a wider net
        return best, {**log, "passed": False}

    # ---------------------------------------------------------------- main entry
    def generate_exam(self, prep: PreparedDoc, spec: ExamSpec, seed: int) -> dict:
        t0 = time.perf_counter()
        self.stats = {"calls": {}, "tokens": 0, "llm_s": 0.0, "parse_failures": 0, "llm_errors": 0,
                      "verifier_skipped": 0, "planner_fallback": False}
        rng = random.Random(seed)
        self._bm25 = BM25([c["content"] for c in prep.chunks]) if self.p["retrieval"] == "hybrid" else None
        probe_out = self.ingest_and_retrieve(prep, None)  # ingest + gold retrieval probe
        self.graph: ConceptGraph | None = None
        if self.p["graph"]:
            self.graph = build_graph([c["content"] for c in prep.chunks],
                                     lambda s, u: self._ask(s, u, "graph", seed), spec.language,
                                     self.p["graph_batch_chars"], self.embedder)
        t_plan = time.perf_counter()
        concepts = self._plan(prep, spec, seed)
        slots, spares = allocate_slots(concepts, spec.n_questions, spec.types,
                                       bloom_plan(spec.n_questions, spec.difficulty, rng))
        accepted, logs, replaced, unverified = [], [], 0, 0
        for slot in slots:
            q, log = self._fill_slot(prep, spec, slot, accepted, seed)
            if not log["passed"] and spares:
                spare = spares.pop(0)
                alt, alt_log = self._fill_slot(prep, spec, {**spare, "slot": slot["slot"], "type": slot["type"],
                                                            "bloom": slot["bloom"]}, accepted, seed)
                replaced += 1
                log["replacement"] = alt_log
                if alt is not None and (alt_log["passed"] or q is None
                                        or (question_shape_ok(alt) and not question_shape_ok(q))):
                    q, log["passed"] = alt, alt_log["passed"]
            if q is None:
                logs.append(log)
                continue
            if not log["passed"]:
                unverified += 1
            q["verified"] = log["passed"]
            q["bloom"] = slot["bloom"]
            q["planned_concept"] = slot["concept"]
            accepted.append(q)
            logs.append(log)

        accepted.sort(key=lambda q: BLOOM_ORDER.index(q["bloom"]) if q["bloom"] in BLOOM_ORDER else 9)
        questions_json, used = [], set()
        for q in accepted:
            used.update(q["_ctx"])
            questions_json.append({**{k: v for k, v in q["_raw"].items() if k not in ("citations",)},
                                   "type": q["type"], "bloom": q["bloom"],
                                   "citations": [f"C{i}" for i in q["_cited"]],
                                   "context_ids": q["_ctx"], "verified": q["verified"],
                                   "planned_concept": q["planned_concept"]})
        used_ids = sorted(used)
        calls = sum(self.stats["calls"].values())
        return {
            "query": f"blueprint: {spec.n_questions} x {spec.types}, {spec.difficulty}",
            "prompt_version": BP_PROMPT_VERSION, "raw_text": None,
            "raw_json": {"title": "Mimir AI Vizsga", "format": "pdf", "questions": questions_json},
            "model_used": f"{self.llm.provider}:{self.llm.model}",
            "llm": {"calls": calls, "calls_by_stage": self.stats["calls"], "tokens": self.stats["tokens"],
                    "parse_failures": self.stats["parse_failures"], "errors": self.stats["llm_errors"]},
            "retrieved": [{"rank": r + 1, "score": None, "text": prep.chunks[i]["content"], "chunk_index": i}
                          for r, i in enumerate(used_ids)],
            "probe": probe_out["probe"],
            "context_text": "\n\n".join(prep.chunks[i]["content"] for i in used_ids),
            "blueprint": {"n_concepts_planned": len(concepts), "slots": len(slots), "replacements": replaced,
                          "unverified": unverified, "verifier_skipped": self.stats["verifier_skipped"],
                          "planner_fallback": self.stats["planner_fallback"],
                          "graph": self.graph.stats() if self.graph else None, "slot_logs": logs,
                          "settings": {k: self.p[k] for k in DEFAULTS}},
            "timings": {**probe_out["timings"], "plan_s": time.perf_counter() - t_plan,
                        "generate_s": time.perf_counter() - t0, "llm_s": self.stats["llm_s"]},
        }
