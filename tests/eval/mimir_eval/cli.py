"""Command line: python -m mimir_eval <command> ...  (run from tests/eval)."""
from __future__ import annotations

import argparse
import os
import sys

from .config import JUDGE_DEFAULTS, load_config


def _load_dotenv() -> None:
    """Pick up OE_GENAI_API_KEY etc. from the repo's .env without extra dependencies."""
    from .config import REPO_ROOT
    env = REPO_ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def cmd_check(a) -> int:
    from .dataset import load_dataset
    from .llm import LLMClient
    from .services import MimirServices
    cfg = load_config(a.config)
    ok = True
    print(f"config: {cfg['name']}  pipeline={cfg['pipeline']['kind']}  chunking={cfg['chunking']['mode']}")
    ds = load_dataset(cfg["dataset"])
    docs = ds.select(cfg["documents"])
    n_gold = sum(1 for d in docs if d.gold())
    print(f"dataset {ds.version}: {len(docs)} documents, {n_gold} with gold questions")
    svc = MimirServices(**cfg["services"])
    for name, state in svc.health().items():
        print(f"  service {name:11s} {state}")
        ok &= state == "ok"
    svc.close()
    targets = [("generator", cfg["generator"])] if cfg["pipeline"]["kind"] != "naive_service" else []
    if a.judge_model:
        targets.append(("judge", {**JUDGE_DEFAULTS, "provider": a.judge_provider, "model": a.judge_model}))
    for role, lc in targets:
        try:
            r = LLMClient(**{**lc, "max_retries": 0}).chat(
                [{"role": "user", "content": 'Reply with {"ok": true}'}], json_mode=True, seed=1)
            print(f"  {role:9s} {lc['provider']}:{lc['model']} ok ({r.latency_s:.1f}s)")
        except Exception as e:
            ok = False
            print(f"  {role:9s} {lc['provider']}:{lc['model']} FAILED: {e}")
    print("ready" if ok else "NOT ready - fix the lines above before running")
    return 0 if ok else 1


def cmd_run(a) -> int:
    from .runner import run_experiment
    run_experiment(a.config, a.results, resume=a.resume, only_docs=a.docs, max_docs=a.max_docs)
    return 0


def cmd_score(a) -> int:
    from .scoring import score_run
    jc = {"provider": a.judge_provider, "model": a.judge_model}
    for rd in a.run_dirs:
        score_run(rd, judge_cfg=jc, use_judge=not a.no_judge, embedder=a.embedder, max_exams=a.max_exams,
                  workers=a.workers)
    return 0


def cmd_rate_export(a) -> int:
    from .rating import export_sheets
    export_sheets(a.run_dirs, a.out, n_per_run=a.n_per_run, n_raters=a.raters,
                  n_calibration=a.calibration, seed=a.seed)
    return 0


def cmd_rate_import(a) -> int:
    from .rating import import_sheets
    import_sheets(a.sheets, a.key, a.out)
    return 0


def cmd_analyze(a) -> int:
    from .analysis import analyze
    pairs = []
    for c in a.compare or []:
        if len(c) != 2:
            raise SystemExit("--compare takes two arm names")
        pairs.append((c[0], c[1]))
    analyze(a.runs, a.name, pairs, a.ratings, a.out)
    return 0


def cmd_import(a) -> int:
    from . import importers
    if a.dataset == "eduqg":
        importers.import_eduqg(a.source or "all", n=a.n or 12, seed=a.seed, min_gold=a.min_gold)
    else:
        importers.import_milqa(a.source or importers.MILQA_URL, n=a.n or 24, seed=a.seed, min_gold=a.min_gold,
                               titles=a.titles)
    return 0


def cmd_view(a) -> int:
    from .viewer import build_viewer
    build_viewer(a.results, a.out)
    return 0


def cmd_report(a) -> int:
    from .report import build_report
    build_report(a.results, a.name, a.arms, a.out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mimir_eval", description="Mimir evaluation harness (TDK)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("check", help="ping services and models for a config")
    s.add_argument("config")
    s.add_argument("--judge-provider", default=JUDGE_DEFAULTS["provider"])
    s.add_argument("--judge-model", default=None, help="also test this judge model")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("run", help="generate exams for every document x seed")
    s.add_argument("config")
    s.add_argument("--results", default="results")
    s.add_argument("--resume", help="existing run dir: only redo missing/failed exams")
    s.add_argument("--docs", nargs="+", help="only these document ids")
    s.add_argument("--max-docs", type=int, help="first N documents (smoke test)")
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("score", help="automatic metrics + LLM judge")
    s.add_argument("run_dirs", nargs="+")
    s.add_argument("--judge-provider", default=JUDGE_DEFAULTS["provider"])
    s.add_argument("--judge-model", default=JUDGE_DEFAULTS["model"])
    s.add_argument("--no-judge", action="store_true", help="only metrics that need no LLM")
    s.add_argument("--embedder", default="e5", help="e5 (default) | bow (tests only) | a HF model name")
    s.add_argument("--max-exams", type=int)
    s.add_argument("--workers", type=int, default=8, help="parallel judge requests (default 8)")
    s.set_defaults(fn=cmd_score)

    s = sub.add_parser("rate-export", help="blind xlsx rating sheets for teachers")
    s.add_argument("run_dirs", nargs="+")
    s.add_argument("--out", default="ratings")
    s.add_argument("--n-per-run", type=int, default=30)
    s.add_argument("--raters", type=int, default=3)
    s.add_argument("--calibration", type=int, default=10)
    s.add_argument("--seed", type=int, default=7)
    s.set_defaults(fn=cmd_rate_export)

    s = sub.add_parser("rate-import", help="read filled rating sheets")
    s.add_argument("sheets", nargs="+")
    s.add_argument("--key", default="ratings/rating_key.csv")
    s.add_argument("--out", default="ratings/ratings.csv")
    s.set_defaults(fn=cmd_rate_import)

    s = sub.add_parser("import", help="build documents + gold questions from EduQG (EN) or MILQA (HU)")
    s.add_argument("dataset", choices=["eduqg", "milqa"])
    s.add_argument("--source", help="eduqg: all (default) | valid | train | a local json; milqa: local json or URL")
    s.add_argument("--n", type=int, help="number of documents (default: 12 EduQG, 24 MILQA)")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--min-gold", type=int, default=4, help="skip documents with fewer gold questions")
    s.add_argument("--titles", nargs="+", help="milqa: only these Wikipedia article titles")
    s.set_defaults(fn=cmd_import)

    s = sub.add_parser("view", help="HTML page to read the generated exams (results/viewer.html)")
    s.add_argument("--results", default="results")
    s.add_argument("--out", help="output file (default: <results>/viewer.html)")
    s.set_defaults(fn=cmd_view)

    s = sub.add_parser("report", help="TDK-ready Hungarian figures + results text (report/)")
    s.add_argument("--results", default="results")
    s.add_argument("--name", help="subfolder, e.g. pilot")
    s.add_argument("--arms", nargs="+", help="only these arms (default: latest run of every arm)")
    s.add_argument("--out", default="report")
    s.set_defaults(fn=cmd_report)

    s = sub.add_parser("analyze", help="tables, statistics and figures")
    s.add_argument("runs", nargs="+", help="scored run dirs, optionally ARM=dir")
    s.add_argument("--name", default="latest")
    s.add_argument("--compare", nargs=2, action="append", metavar=("A", "B"))
    s.add_argument("--ratings", help="ratings.csv from rate-import")
    s.add_argument("--out", default="analysis")
    s.set_defaults(fn=cmd_analyze)
    return p


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # Windows consoles and Hungarian text
    args = build_parser().parse_args(argv)
    return args.fn(args)
