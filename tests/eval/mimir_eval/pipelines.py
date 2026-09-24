"""Pipeline adapters. Each turns (document, exam spec, seed) into one exam record.

- naive_direct  : Wellspring -> RuneCarver (or fixed chunks) -> Bifrost ingest/search,
                  then the *production* v1 prompt sent straight to a configurable LLM.
                  This is E0: same retrieval and prompt as production, but model,
                  temperature and seed are controlled.
- naive_service : the full production chain including Bifrost /generate (model chosen by
                  Bifrost's own fallback list). Useful as an end-to-end smoke test; not
                  reproducible enough for the paper tables.
- blueprint     : planner -> per-slot retrieval -> one question per call -> verifier ->
                  assembler (ROADMAP section 5); see mimir_eval/blueprint/. Arms E1-E3.
"""
from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass

from .config import REPO_ROOT
from .dataset import Document
from .llm import LLMClient
from .schema import is_error_fallback, normalize_exam, parse_llm_json
from .services import MimirServices

sys.path.insert(0, str(REPO_ROOT / "services" / "bifrost"))
try:
    from prompts import PROMPT_VERSION, SYSTEM_PROMPT, build_naive_prompt  # type: ignore  # noqa: E402
except ImportError:  # pragma: no cover - only if services/bifrost/prompts.py is missing
    raise ImportError("services/bifrost/prompts.py not found; the harness needs the production prompt")

TYPE_HU = {"mcq": "feleletválasztós (mcq)", "tf": "igaz-hamis (tf)", "open": "kifejtős (open)"}
DIFF_HU = {"easy": "kezdő (könnyű)", "medium": "közepes", "hard": "haladó (nehéz)"}


def build_query(n: int, types: list[str], difficulty: str, language: str) -> str:
    """The user request text, phrased the way a teacher would type it in the UI."""
    kinds = ", ".join(TYPE_HU[t] for t in types)
    q = (f"Készíts pontosan {n} darab vizsgakérdést, típus: {kinds}. "
         f"Nehézségi szint: {DIFF_HU.get(difficulty, difficulty)}.")
    if language == "en":
        q += " A kérdéseket és a válaszokat angol nyelven írd meg."
    return q


def fixed_chunks(text: str, size: int = 1000, overlap: int = 0) -> list[dict]:
    """Baseline chunker: windows of ~size chars, cut at the last whitespace."""
    text = re.sub(r"\s+", " ", text).strip()
    out, i = [], 0
    while i < len(text):
        end = min(i + size, len(text))
        if end < len(text):
            cut = text.rfind(" ", i + size // 2, end)
            end = cut if cut != -1 else end
        out.append({"type": "narrative", "content": text[i:end].strip(), "metadata": {"qa_score": 10}})
        if end >= len(text):
            break
        i = max(end - overlap, i + 1)
    return [c for c in out if c["content"]]


@dataclass
class ExamSpec:
    n_questions: int
    types: list[str]
    difficulty: str
    language: str

    @classmethod
    def for_document(cls, exam_cfg: dict, doc: Document) -> "ExamSpec":
        diff = exam_cfg["difficulty"]
        lang = exam_cfg["language"]
        return cls(exam_cfg["n_questions"], list(exam_cfg["types"]),
                   doc.difficulty if diff == "from_document" else diff,
                   doc.language if lang == "from_document" else lang)


class PreparedDoc:
    """Extraction + chunking done once per document, reused for every seed."""

    def __init__(self, doc: Document, text: str, chunks: list[dict], timings: dict):
        self.doc, self.text, self.chunks, self.timings = doc, text, chunks, timings


class BasePipeline:
    kind = "base"
    implemented = True

    def __init__(self, cfg: dict, services: MimirServices, llm: LLMClient | None):
        self.cfg, self.services, self.llm = cfg, services, llm

    # -- shared steps -----------------------------------------------------
    def prepare(self, doc: Document) -> PreparedDoc:
        ch = self.cfg["chunking"]
        text, t_extract = self.services.extract(doc.path.name, doc.read_bytes())
        if not text.strip():
            raise RuntimeError("Wellspring returned no text")
        if ch["mode"] == "fixed":
            t0 = time.perf_counter()
            chunks = fixed_chunks(text, ch["target_size"], ch["overlap"])
            t_chunk = time.perf_counter() - t0
        else:
            chunks, t_chunk = self.services.chunk(doc.path.name, doc.extension, text, method=ch["method"],
                                                  threshold=ch["threshold"], target_size=ch["target_size"],
                                                  encoder=ch["encoder"])
        if not chunks:
            raise RuntimeError("no chunks produced")
        return PreparedDoc(doc, text, chunks, {"extract_s": t_extract, "chunk_s": t_chunk})

    def _chunk_index(self, prep: PreparedDoc, text: str) -> int | None:
        for i, c in enumerate(prep.chunks):
            if c.get("content", "").strip() == (text or "").strip():
                return i
        return None

    def ingest_and_retrieve(self, prep: PreparedDoc, query: str | None) -> dict:
        """Ingest the chunks, run the gold retrieval probe, then (if query) the top-k search."""
        p = self.cfg["pipeline"]
        _, t_ingest = self.services.ingest(prep.chunks)
        probe = []
        if p["retrieval_probe"]:
            for g in prep.doc.gold():
                if not g["evidence"]:
                    continue
                hits, _ = self.services.search(g["text"], p["probe_k"])
                probe.append({"gold_qid": g["qid"],
                              "retrieved_idx": [self._chunk_index(prep, h["payload"].get("text", "")) for h in hits]})
        if query is None:
            return {"retrieved": [], "probe": probe, "context_text": "", "timings": {"ingest_s": t_ingest}}
        hits, t_ret = self.services.search(query, p["retrieval_k"])
        retrieved = [{"rank": r + 1, "score": h.get("score"), "text": h["payload"].get("text", ""),
                      "chunk_index": self._chunk_index(prep, h["payload"].get("text", ""))}
                     for r, h in enumerate(hits)]
        return {"retrieved": retrieved, "probe": probe,
                "context_text": "\n\n".join(r["text"] for r in retrieved),
                "timings": {"ingest_s": t_ingest, "retrieve_s": t_ret}}

    def generate_exam(self, prep: PreparedDoc, spec: ExamSpec, seed: int) -> dict:
        raise NotImplementedError


class NaiveDirectPipeline(BasePipeline):
    kind = "naive_direct"

    def generate_exam(self, prep, spec, seed):
        query = build_query(spec.n_questions, spec.types, spec.difficulty, spec.language)
        r = self.ingest_and_retrieve(prep, query)
        prompt = build_naive_prompt(r["context_text"], query, "pdf")
        res = self.llm.chat([{"role": "system", "content": SYSTEM_PROMPT},
                             {"role": "user", "content": prompt}], json_mode=True, seed=seed)
        out = {"query": query, "prompt_version": PROMPT_VERSION, "raw_text": res.text,
               "model_used": f"{self.llm.provider}:{self.llm.model}",
               "llm": {"calls": 1, "prompt_tokens": res.prompt_tokens,
                       "completion_tokens": res.completion_tokens, "attempts": res.attempts},
               **{k: r[k] for k in ("retrieved", "probe", "context_text")},
               "timings": {**r["timings"], "generate_s": res.latency_s}}
        try:
            out["raw_json"] = parse_llm_json(res.text)
        except Exception as e:
            out["raw_json"], out["parse_error"] = None, str(e)
        return out


class NaiveServicePipeline(BasePipeline):
    kind = "naive_service"

    def generate_exam(self, prep, spec, seed):
        query = build_query(spec.n_questions, spec.types, spec.difficulty, spec.language)
        r = self.ingest_and_retrieve(prep, query)      # same search Bifrost does internally
        job, t_gen = self.services.generate(query, self.cfg["pipeline"]["retrieval_k"])
        data = job.get("data") if job.get("status") == "completed" else None
        meta = (data or {}).get("metadata", {}) if isinstance(data, dict) else {}
        return {"query": query, "prompt_version": PROMPT_VERSION, "raw_text": None, "raw_json": data,
                "model_used": meta.get("model_used", "unknown"),
                "service_error": job.get("error"),
                "llm": {"calls": 1},
                **{k: r[k] for k in ("retrieved", "probe", "context_text")},
                "timings": {**r["timings"], "generate_s": t_gen}}


PIPELINES = {p.kind: p for p in (NaiveDirectPipeline, NaiveServicePipeline)}


def pipeline_class(kind: str):
    """Blueprint lives in its own package (imported lazily to avoid a circular import)."""
    if kind == "blueprint":
        from .blueprint.pipeline import BlueprintPipeline
        return BlueprintPipeline
    return PIPELINES[kind]


def finalize(out: dict) -> dict:
    """Normalise questions and classify the outcome."""
    raw = out.get("raw_json")
    if raw is None:
        status = "parse_error" if out.get("raw_text") else "error"
    elif is_error_fallback(raw):
        status = "fallback"          # Bifrost's hard-coded "models overloaded" exam
    else:
        status = "ok"
    out["status"] = status
    out["questions"] = normalize_exam(raw) if status == "ok" else []
    return out
