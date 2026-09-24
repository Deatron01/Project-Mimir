"""Experiment configuration (YAML) with defaults.

A config describes ONE experiment arm (e.g. E0). Everything that can change a result
lives here, and the whole resolved config is saved next to the results.
"""
from __future__ import annotations

import copy
import os
from pathlib import Path

import yaml

EVAL_ROOT = Path(__file__).resolve().parent.parent      # tests/eval
REPO_ROOT = EVAL_ROOT.parent.parent                       # Project-Mimir

DEFAULTS: dict = {
    "name": None,                 # short id used in tables, e.g. "E0"
    "description": "",
    "dataset": "dataset/manifest.yaml",
    "documents": "all",           # "all" | list of document ids
    "seeds": [1, 2, 3],
    "exam": {
        "n_questions": 10,
        "types": ["mcq"],         # mcq | tf | open
        "difficulty": "from_document",   # easy | medium | hard | from_document
        "language": "from_document",     # hu | en | from_document
    },
    "pipeline": {
        "kind": "naive_direct",   # naive_direct | naive_service | blueprint
        "retrieval_k": 3,
        "retrieval_probe": True,  # extra /search calls with gold questions -> recall@k
        "probe_k": 10,
    },
    "chunking": {
        "mode": "service",        # service (RuneCarver) | fixed (harness-side baseline)
        "method": "percentile",   # percentile | std   (service mode)
        "threshold": None,        # percentile value or std factor; None = service default
        "target_size": 1000,      # chars; also the window for fixed mode
        "overlap": 0,             # fixed mode only
        "encoder": "window",      # window (fixed RuneCarver) | legacy (old 512-token truncation, E5a)
    },
    "generator": {
        "provider": "ollama",     # ollama | genai | openai_compat | mock
        "model": "qwen2.5:7b",
        "temperature": 0.2,
        "num_ctx": 8192,          # every prompt fits; 16384 only made Ollama slower (AI-18)
        "timeout_s": 600,
    },
    "services": {
        "wellspring": "http://localhost:8001",
        "runecarver": "http://localhost:8002",
        "bifrost": "http://localhost:8003",
        "timeout_s": 600,
        "poll_interval_s": 2.0,
    },
    "monitor_vram": True,
}

JUDGE_DEFAULTS: dict = {
    "provider": "genai",
    "model": "gpt-oss:120b",      # use a different family than the generator
    "temperature": 0.0,
    "timeout_s": 300,
    "max_context_chars": 24000,   # cap on the source text shown to the judge
    "context": "question",        # question: the chunks the question was written from (else the retrieved
                                  # context); document: the full document when it fits (slower, judge-v1)
    "reasoning": "low",           # gpt-oss reasoning effort, sent as "Reasoning: <level>"; None = model default
}

PROVIDERS: dict = {
    "ollama": {"base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"), "api_key_env": None},
    "genai": {"base_url": os.getenv("OE_GENAI_BASE_URL", "https://genai.uni-obuda.hu/api"),
              "api_key_env": "OE_GENAI_API_KEY"},
    "openai_compat": {"base_url": os.getenv("OPENAI_BASE_URL", ""), "api_key_env": "OPENAI_API_KEY"},
    "mock": {"base_url": "", "api_key_env": None},
}


def deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: str | Path) -> dict:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cfg = deep_merge(DEFAULTS, raw)
    if not cfg["name"]:
        cfg["name"] = path.stem
    cfg["_config_path"] = str(path)
    validate(cfg)
    return cfg


def validate(cfg: dict) -> None:
    ex = cfg["exam"]
    bad = set(ex["types"]) - {"mcq", "tf", "open"}
    if bad:
        raise ValueError(f"unknown question types: {bad}")
    if cfg["pipeline"]["kind"] not in {"naive_direct", "naive_service", "blueprint"}:
        raise ValueError(f"unknown pipeline.kind: {cfg['pipeline']['kind']}")
    if cfg["chunking"]["mode"] not in {"service", "fixed"}:
        raise ValueError(f"unknown chunking.mode: {cfg['chunking']['mode']}")
    if cfg["chunking"]["encoder"] not in {"window", "legacy"}:
        raise ValueError(f"unknown chunking.encoder: {cfg['chunking']['encoder']}")
    if cfg["pipeline"].get("retrieval", "dense") not in {"dense", "hybrid"}:
        raise ValueError(f"unknown pipeline.retrieval: {cfg['pipeline'].get('retrieval')}")
    if cfg["chunking"]["method"] not in {"percentile", "std"}:
        raise ValueError(f"unknown chunking.method: {cfg['chunking']['method']}")
    if cfg["generator"]["provider"] not in PROVIDERS:
        raise ValueError(f"unknown generator.provider: {cfg['generator']['provider']}")
    if cfg["pipeline"]["kind"] == "naive_service" and cfg["chunking"]["mode"] == "fixed":
        raise ValueError("naive_service uses the real service chain; use naive_direct for fixed chunking")


def resolve(path: str | Path, base: Path = EVAL_ROOT) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (base / p).resolve()
