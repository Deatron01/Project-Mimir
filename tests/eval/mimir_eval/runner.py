"""`run`: execute one experiment config over every document x seed."""
from __future__ import annotations

import platform
import time
import traceback
from datetime import datetime
from pathlib import Path

from .config import EVAL_ROOT, REPO_ROOT, load_config, resolve
from .dataset import load_dataset
from .llm import LLMClient
from .pipelines import ExamSpec, finalize, pipeline_class
from .schema import exam_format
from .services import MimirServices
from .util import append_jsonl, git_info, read_jsonl, write_json
from .vram import VramMonitor, gpu_info, ollama_residency


def run_experiment(config_path: str, results_root: str | Path = "results", resume: str | None = None,
                   only_docs: list[str] | None = None, max_docs: int | None = None) -> Path:
    cfg = load_config(config_path)
    ds = load_dataset(cfg["dataset"])
    docs = ds.select(only_docs or cfg["documents"])
    if max_docs:
        docs = docs[:max_docs]

    if resume:
        out_dir = resolve(resume)
        run_id = out_dir.name
    else:
        run_id = f"{cfg['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        out_dir = resolve(results_root) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    exams_path = out_dir / "exams.jsonl"
    done = {(r["doc_id"], r["seed"]) for r in read_jsonl(exams_path) if r.get("status") == "ok"}

    kind = cfg["pipeline"]["kind"]
    cls = pipeline_class(kind)
    if not cls.implemented:
        raise SystemExit(f"pipeline '{kind}' is not implemented yet")
    services = MimirServices(**cfg["services"])
    llm = None if kind == "naive_service" else LLMClient.from_config(cfg["generator"])
    pipeline = cls(cfg, services, llm)

    meta = {"run_id": run_id, "config": cfg, "dataset_version": ds.version,
            "n_documents": len(docs), "seeds": cfg["seeds"],
            "git": git_info(REPO_ROOT), "python": platform.python_version(),
            "host": platform.node(), "started": datetime.now().isoformat(timespec="seconds"),
            "generator": llm.describe() if llm else {"provider": "bifrost-service"},
            "hardware": {"gpus": gpu_info(), "platform": platform.platform()}}
    write_json(out_dir / "run.json", meta)

    total = len(docs) * len(cfg["seeds"])
    print(f"[run] {run_id}: {len(docs)} docs x {len(cfg['seeds'])} seeds = {total} exams -> {out_dir}")
    counts: dict[str, int] = {}
    i = 0
    for doc in docs:
        spec = ExamSpec.for_document(cfg["exam"], doc)
        todo = [s for s in cfg["seeds"] if (doc.id, s) not in done]
        i += len(cfg["seeds"]) - len(todo)
        if not todo:
            continue
        try:
            prep = pipeline.prepare(doc)
        except Exception as e:
            for seed in todo:
                i += 1
                _write_error(exams_path, run_id, cfg, doc, seed, spec, e)
                counts["error"] = counts.get("error", 0) + 1
            print(f"  ! {doc.id}: preparation failed: {e}")
            continue
        for seed in todo:
            i += 1
            t0 = time.perf_counter()
            base = _base_record(run_id, cfg, doc, seed, spec)
            try:
                with VramMonitor(enabled=cfg["monitor_vram"]) as vm:
                    out = pipeline.generate_exam(prep, spec, seed)
                out = finalize(out)
                resident = (ollama_residency(llm.base_url)
                            if llm and llm.provider == "ollama" and cfg["monitor_vram"] else None)
                rec = {**base, **out,
                       "doc_text": prep.text, "chunks": [c.get("content", "") for c in prep.chunks],
                       "n_chunks": len(prep.chunks),
                       "timings": {**prep.timings, **out["timings"], "total_s": time.perf_counter() - t0},
                       "vram_peak_mib": vm.peak_mib, "vram_baseline_mib": vm.baseline_mib,
                       "ollama_ps": resident,
                       "format": exam_format(out["questions"], spec.n_questions, spec.types)}
            except Exception as e:
                rec = {**base, "status": "error", "error": f"{type(e).__name__}: {e}",
                       "traceback": traceback.format_exc(limit=5), "questions": []}
            append_jsonl(exams_path, rec)
            counts[rec["status"]] = counts.get(rec["status"], 0) + 1
            fmt = rec.get("format", {})
            print(f"  [{i}/{total}] {doc.id} seed={seed} status={rec['status']} "
                  f"q={fmt.get('n_generated', 0)}/{spec.n_questions} "
                  f"t={rec.get('timings', {}).get('total_s', 0):.1f}s")

    services.close()
    meta.update({"finished": datetime.now().isoformat(timespec="seconds"), "status_counts": counts})
    write_json(out_dir / "run.json", meta)
    if counts.get("fallback") or counts.get("error") or counts.get("parse_error"):
        print(f"[run] WARNING: {counts}. parse_error/fallback count as failed exams (format compliance = 0); "
              f"status=error (service or network down) is excluded from analysis - retry those with "
              f"--resume {out_dir}")
    print(f"[run] done: {counts}")
    return out_dir


def _base_record(run_id, cfg, doc, seed, spec) -> dict:
    return {"run_id": run_id, "arm": cfg["name"], "doc_id": doc.id, "seed": seed,
            "language": spec.language, "difficulty": spec.difficulty, "subject": doc.subject,
            "n_requested": spec.n_questions, "types": spec.types,
            "created": datetime.now().isoformat(timespec="seconds")}


def _write_error(path, run_id, cfg, doc, seed, spec, e) -> None:
    append_jsonl(path, {**_base_record(run_id, cfg, doc, seed, spec), "status": "error",
                        "error": f"prepare: {type(e).__name__}: {e}", "questions": []})


__all__ = ["run_experiment", "EVAL_ROOT"]
