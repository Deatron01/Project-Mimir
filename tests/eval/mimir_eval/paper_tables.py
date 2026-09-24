"""LaTeX tables and plot data for the paper, written by `report` into <report>/latex/.

  tab_main.tex          one row per arm: quality index, the four rates, coverage, leakage, unverified per
                        exam, mean LLM calls and median minutes per exam
  tab_verifier.tex      judge outcomes of the questions the verifier passed vs flagged (pooled)
  tab_verifier_arms.tex the verifier as a classifier of "grounded", per arm: precision, recall, Cohen κ
  tab_leakage.tex       answer leakage per arm: key in stem, stem not a question, judge scores of leaky items
  tab_significance.tex  paired Wilcoxon tests of the key steps (Holm-corrected), when both arms were run
  fig_quality_time.dat  arm, median minutes, index, local (a pgfplots `table`)
  paper_numbers.json    every number above, for the text

Each .tex file holds only the tabular, so the paper keeps its own caption and label:
    \\begin{table}[t]\\centering\\caption{...}\\label{...}\\footnotesize\\input{tables/tab_main}\\end{table}
Older runs lack some question fields; the verifier verdict is joined from exams.jsonl and the leakage
flags are recomputed from the question text, so the pilot's tables come out of the same code.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from .schema import key_in_stem, stem_is_question
from .stats import cohen_kappa
from .util import read_jsonl

ARM_ORDER = ["B-doc-L", "B-doc-S", "E0", "E1", "E2", "E2x", "E2f", "E2h", "E3", "E4", "E4b",
             "E5a", "E5b", "E5c"]
RATES = [("format_compliant", "Form."), ("grounding_rate", "Grnd."), ("blind_answerability", "Blind"),
         ("distractor_validity", "Dist."), ("coverage", "Cov.")]


def order_arms(arms) -> list[str]:
    arms = list(dict.fromkeys(arms))
    return [a for a in ARM_ORDER if a in arms] + sorted(a for a in arms if a not in ARM_ORDER)


def _nan(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def rate(v) -> str:
    return "--" if _nan(v) else f"{round(100 * v)}"


def num(v, nd: int, plus: bool = False) -> str:
    if _nan(v):
        return "--"
    t = f"{v:+.{nd}f}" if plus else f"{v:.{nd}f}"
    return "$-$" + t[1:] if t.startswith("-") else t        # a real minus sign, not a hyphen


def tex(s: str) -> str:
    return str(s).replace("\\", "\\textbackslash{}").replace("_", "\\_").replace("%", "\\%").replace("&", "\\&")


# ---------------------------------------------------------------- data
def enrich_questions(root: Path, qs: pd.DataFrame) -> pd.DataFrame:
    """Add the verifier's verdict (and whether it ran) from exams.jsonl and the leakage flags."""
    if qs.empty:
        return qs
    qs = qs.copy()
    verdict: dict[str, tuple] = {}
    for rid in qs["run_id"].dropna().unique():
        p = root / rid / "exams.jsonl"
        if not p.exists():
            continue
        for ex in read_jsonl(p):                   # a resumed exam appears again later: the last one wins
            on = ((ex.get("blueprint") or {}).get("settings") or {}).get("verifier")
            for q in ex.get("questions") or []:
                verdict[f"{ex['run_id']}|{ex['doc_id']}|{ex['seed']}|{q['qid']}"] = (q.get("verified"), on)
    if verdict:
        qs["verified"] = [verdict.get(u, (None, None))[0] for u in qs["uid"]]
        qs["verifier_on"] = [verdict.get(u, (None, None))[1] for u in qs["uid"]]
    for c in ("verified", "verifier_on"):
        if c not in qs:
            qs[c] = None
    rows = qs[["type", "text", "key"]].to_dict("records")
    qs["key_in_stem"] = [key_in_stem(r) for r in rows]
    qs["stem_is_question"] = [stem_is_question(r) for r in rows]
    return qs


def _per_doc_mean(ex: pd.DataFrame, arm: str, col: str) -> float:
    if col not in ex:
        return math.nan
    s = ex[ex.arm == arm].groupby("doc_id")[col].apply(lambda v: pd.to_numeric(v, errors="coerce").mean())
    return float(s.dropna().mean()) if s.notna().any() else math.nan


def _share(s: pd.Series) -> float:
    s = s.dropna()
    return float(s.astype(bool).mean()) if len(s) else math.nan


def main_rows(ex: pd.DataFrame, summary: pd.DataFrame, qs: pd.DataFrame) -> list[dict]:
    s = summary.set_index("arm")
    rows = []
    for arm in order_arms(summary["arm"]):
        r = s.loc[arm]
        q = qs[qs.arm == arm] if len(qs) else qs
        rows.append({"arm": arm, "local": bool(r["helyi"]), "index": r["qi"], "ci_lo": r["ci_lo"],
                     "ci_hi": r["ci_hi"], "n_docs": int(r["n_docs"]), "n_exams": int(r["n_exams"]),
                     **{c: r.get(c, math.nan) for c, _ in RATES},
                     "unverified": _per_doc_mean(ex, arm, "unverified"),
                     "truncated_share": _per_doc_mean(ex, arm, "truncated_share"),
                     "leakage": _share(q["key_in_stem"]) if len(q) else math.nan,
                     "non_question": 1 - _share(q["stem_is_question"]) if len(q) else math.nan,
                     "calls": _per_doc_mean(ex, arm, "llm_calls"), "minutes": r["ido_median_s"] / 60})
    return rows


def verifier_rows(qs: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    """Pooled judge outcomes by verdict, and per arm the verdict scored as a classifier of 'grounded'."""
    if qs.empty or "verifier_on" not in qs:
        return [], []
    v = qs[(qs["verifier_on"] == True) & qs["verified"].notna()].copy()   # noqa: E712 (None-safe)
    if v.empty:
        return [], []
    v["verified"] = v["verified"].astype(bool)
    pooled = []
    for name, g in (("passed", v[v.verified]), ("flagged", v[~v.verified])):
        pooled.append({"verdict": name, "n": len(g), "grounded": _share(g.get("grounded", pd.Series(dtype=float))),
                       "blind_correct": _share(g.get("blind_correct", pd.Series(dtype=float))),
                       "would_use": _share(g.get("judge_would_use", pd.Series(dtype=float)))})
    per_arm = []
    for arm in order_arms(v["arm"]):
        g = v[(v.arm == arm) & v["grounded"].notna()] if "grounded" in v else v.iloc[0:0]
        if g.empty:
            continue
        pred, true = g["verified"].astype(bool), g["grounded"].astype(bool)
        tp = int((pred & true).sum())
        per_arm.append({"arm": arm, "n": len(g), "pass_rate": float(pred.mean()),
                        "precision": tp / pred.sum() if pred.sum() else math.nan,
                        "recall": tp / true.sum() if true.sum() else math.nan,
                        "kappa": cohen_kappa(pred.tolist(), true.tolist())})
    return pooled, per_arm


def leakage_rows(qs: pd.DataFrame) -> list[dict]:
    rows = []
    if qs.empty:
        return rows
    for arm in order_arms(qs["arm"]):
        g = qs[qs.arm == arm]
        leak = g[g["key_in_stem"]]
        rows.append({"arm": arm, "n": len(g), "leakage": _share(g["key_in_stem"]),
                     "non_question": 1 - _share(g["stem_is_question"]),
                     "judge_correctness_leaky": float(pd.to_numeric(leak.get("judge_correctness"),
                                                                    errors="coerce").mean())
                     if len(leak) and "judge_correctness" in leak else math.nan})
    return rows


# ---------------------------------------------------------------- LaTeX
def _tabular(spec: str, header: list[str], body: list[list[str]], sources: list[str]) -> str:
    L = [f"% generated by `python -m mimir_eval report` from {', '.join(sorted(sources))}; do not edit",
         f"\\begin{{tabular}}{{{spec}}}", "\\toprule", " & ".join(header) + " \\\\", "\\midrule"]
    L += [" & ".join(r) + " \\\\" for r in body]
    L += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(L)


def write_latex(out: Path, ex: pd.DataFrame, summary: pd.DataFrame, qs: pd.DataFrame, root: Path,
                sig: pd.DataFrame | None = None) -> Path:
    d = out / "latex"
    d.mkdir(parents=True, exist_ok=True)
    qs = enrich_questions(root, qs)
    sources = list(ex["run_dir"].unique())
    pilot = ex["doc_id"].nunique() < 6
    main = main_rows(ex, summary, qs)

    header = ["Arm", "Index"] + ([] if pilot else ["95\\,\\% CI"]) + [h for _, h in RATES] + \
             ["Leak.", "Unv.", "Calls", "Min"]
    body = []
    for r in main:
        row = [tex(r["arm"]), num(r["index"], 2)]
        if not pilot:
            row.append("--" if _nan(r["ci_lo"]) else f"{r['ci_lo']:.2f}--{r['ci_hi']:.2f}")
        row += [rate(r[c]) for c, _ in RATES]
        row += [rate(r["leakage"]), num(r["unverified"], 1), num(r["calls"], 0), num(r["minutes"], 1)]
        body.append(row)
    n_num = len(header) - 2
    (d / "tab_main.tex").write_text(_tabular("@{}l" + "c" * n_num + "r@{}", header, body, sources), encoding="utf-8")

    pooled, per_arm = verifier_rows(qs)
    if pooled:
        body = [[("Passed (verified)" if p["verdict"] == "passed" else "Flagged (unverified)"), str(p["n"]),
                 rate(p["grounded"]), rate(p["blind_correct"]), rate(p["would_use"])] for p in pooled]
        (d / "tab_verifier.tex").write_text(
            _tabular("@{}lcccc@{}", ["Verifier verdict", "$n$", "Grounded", "Blind correct", "Would use"],
                     body, sources), encoding="utf-8")
        body = [[tex(r["arm"]), str(r["n"]), rate(r["pass_rate"]), num(r["precision"], 2), num(r["recall"], 2),
                 num(r["kappa"], 2)] for r in per_arm]
        (d / "tab_verifier_arms.tex").write_text(
            _tabular("@{}lccccc@{}", ["Arm", "$n$", "Passed", "Precision", "Recall", "$\\kappa$"], body, sources),
            encoding="utf-8")

    leak = leakage_rows(qs)
    body = [[tex(r["arm"]), str(r["n"]), rate(r["leakage"]), rate(r["non_question"]),
             num(r["judge_correctness_leaky"], 1)] for r in leak]
    (d / "tab_leakage.tex").write_text(
        _tabular("@{}lcccc@{}", ["Arm", "$n$", "Key in stem", "Not a question", "Judge corr.\\ (leaky)"],
                 body, sources), encoding="utf-8")

    if sig is not None and len(sig):
        body = [[f"{tex(r.new)} vs {tex(r.ref)}", str(r.n_pairs), num(r.mean_a, 2), num(r.mean_b, 2),
                 num(r.mean_diff, 2, plus=True), num(r.r_rb, 2), num(r.p_holm, 3)]
                for r in sig.itertuples()]
        (d / "tab_significance.tex").write_text(
            _tabular("@{}lcccccc@{}", ["Comparison", "$n$", "Ref.", "New", "$\\Delta$", "$r$", "$p_\\mathrm{Holm}$"],
                     body, sources), encoding="utf-8")

    dat = ["arm minutes index local"] + [f"{r['arm']} {r['minutes']:.3f} {r['index']:.3f} {int(r['local'])}"
                                         for r in main if not _nan(r["minutes"]) and not _nan(r["index"])]
    (d / "fig_quality_time.dat").write_text("\n".join(dat) + "\n", encoding="utf-8")

    clean = lambda rows: [{k: (None if _nan(v) else v) for k, v in r.items()} for r in rows]  # noqa: E731
    (d / "paper_numbers.json").write_text(json.dumps(
        {"pilot": pilot, "n_documents": int(ex["doc_id"].nunique()), "runs": sorted(sources),
         "main": clean(main), "verifier_pooled": clean(pooled), "verifier_by_arm": clean(per_arm),
         "leakage": clean(leak),
         "significance": clean(sig.to_dict("records")) if sig is not None else []},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return d
