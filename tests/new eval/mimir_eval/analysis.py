"""`analyze`: turn scored runs (+ teacher ratings) into paper tables, tests and figures."""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .config import resolve  # noqa: E402
from .rubric import CRITERIA  # noqa: E402
from .stats import (bootstrap_ci, cohen_kappa, holm, krippendorff_alpha, paired_wilcoxon,  # noqa: E402
                    spearman)
from .util import read_jsonl  # noqa: E402

# (column, label, higher_is_better)
QUALITY = [
    ("format_compliant", "Format compliance", True),
    ("valid_json", "Valid JSON", True),
    ("grounding_rate", "Grounding rate", True),
    ("blind_answerability", "Blind answerability", True),
    ("distractor_validity", "Distractor validity", True),
    ("meta_reference_rate", "Meta-reference rate", False),
    ("duplicate_rate", "Duplicate rate", False),
    ("coverage", "Section coverage", True),
    ("gold_max_sim_mean", "Gold similarity", True),
    ("recall@1", "Retrieval recall@1", True),
    ("recall@3", "Retrieval recall@3", True),
    ("recall@5", "Retrieval recall@5", True),
    ("mrr", "Retrieval MRR", True),
    *[(f"judge_{c}", f"Judge {c.replace('_', ' ')} (1-5)", True) for c in CRITERIA],
]
COST = [("total_s", "Total time (s)"), ("generate_s", "Generation time (s)"),
        ("vram_peak_mib", "Peak VRAM (MiB)"), ("llm_calls", "LLM calls"),
        ("unverified", "Unverified questions per exam"), ("replacements", "Replaced slots per exam")]
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def load_runs(run_specs: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """run_specs: 'path' or 'ARM=path' (the arm label defaults to the config name)."""
    exams, questions = [], []
    for spec in run_specs:
        arm, _, path = spec.rpartition("=") if "=" in spec else ("", "", spec)
        rd = resolve(path)
        if not (rd / "exam_metrics.csv").exists():
            raise FileNotFoundError(f"{rd}: run `score` first")
        label = arm or json.loads((rd / "run.json").read_text(encoding="utf-8"))["config"]["name"]
        e = pd.read_csv(rd / "exam_metrics.csv")
        e["arm"] = label
        exams.append(e)
        q = pd.DataFrame(read_jsonl(rd / "questions.jsonl"))
        if len(q):
            q["arm"] = label
            questions.append(q)
    ex = pd.concat(exams, ignore_index=True)
    qs = pd.concat(questions, ignore_index=True) if questions else pd.DataFrame()
    return ex, qs


def per_doc(ex: pd.DataFrame, col: str) -> pd.Series:
    """Mean over seeds per (arm, doc) - documents are the unit of analysis."""
    return ex.groupby(["arm", "doc_id"])[col].mean()


def arm_values(ex: pd.DataFrame, col: str, arm: str) -> np.ndarray:
    """Per-document means of one metric for one arm (NaN dropped)."""
    sub = ex[ex.arm == arm]
    if col not in sub or sub.empty:
        return np.array([])
    return sub.groupby("doc_id")[col].apply(lambda v: pd.to_numeric(v, errors="coerce").mean()).dropna().values


def arm_table(ex: pd.DataFrame, arms: list[str]) -> pd.DataFrame:
    rows = []
    for col, label, better in QUALITY:
        if col not in ex or ex[col].isna().all():
            continue
        row = {"metric": label, "column": col, "higher_is_better": better}
        for a in arms:
            m, lo, hi = bootstrap_ci(arm_values(ex, col, a))
            row[a] = m
            row[f"{a} CI"] = f"[{lo:.3f}, {hi:.3f}]" if not math.isnan(lo) else ""
            seed_sd = pd.to_numeric(ex.loc[ex.arm == a, col], errors="coerce").groupby(
                ex.loc[ex.arm == a, "doc_id"]).std().mean()
            row[f"{a} seed SD"] = seed_sd
        rows.append(row)
    return pd.DataFrame(rows)


def cost_table(ex: pd.DataFrame, arms: list[str]) -> pd.DataFrame:
    rows = []
    for col, label in COST:
        if col not in ex or ex[col].isna().all():
            continue
        row = {"metric": label}
        for a in arms:
            v = ex.loc[ex.arm == a, col].dropna().astype(float)
            row[f"{a} p50"] = float(v.median()) if len(v) else math.nan
            row[f"{a} p95"] = float(v.quantile(0.95)) if len(v) else math.nan
            row[f"{a} max"] = float(v.max()) if len(v) else math.nan
        rows.append(row)
    return pd.DataFrame(rows)


def compare(ex: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    rows = []
    for col, label, better in QUALITY:
        if col not in ex or ex[col].isna().all():
            continue
        s = per_doc(ex.assign(**{col: pd.to_numeric(ex[col], errors="coerce")}), col).unstack(0)
        if a not in s or b not in s:
            continue
        both = s[[a, b]].dropna()
        res = paired_wilcoxon(both[a].values, both[b].values)
        rows.append({"metric": label, "higher_is_better": better, **res})
    df = pd.DataFrame(rows)
    if len(df):
        df["p_holm"] = holm(df["p"].tolist())
        df["better"] = [
            (b if (r.mean_diff > 0) == r.higher_is_better else a) if r.mean_diff != 0 else "="
            for r in df.itertuples()]
        df["significant"] = df["p_holm"] < 0.05
    return df


def human_analysis(ratings_csv: str, qs: pd.DataFrame, out: Path) -> dict:
    r = pd.read_csv(resolve(ratings_csv))
    r = r[(r.get("sheet", "Értékelés") == "Értékelés") & (~r["calibration"].fillna(False).astype(bool))]
    res: dict = {"n_ratings": int(len(r)), "n_items": int(r["item_id"].nunique()),
                 "raters": sorted(r["rater"].unique().tolist())}
    alphas = {}
    for c in CRITERIA + ["would_use"]:
        col = f"h_{c}"
        if col not in r or r[col].isna().all():
            continue
        m = r.pivot_table(index="rater", columns="item_id", values=col, aggfunc="first")
        m = m.astype(float)
        alphas[c] = krippendorff_alpha(m.values, "nominal" if c == "would_use" else "ordinal")
    res["krippendorff_alpha"] = alphas
    item = r.groupby(["uid", "arm"]).agg({f"h_{c}": "mean" for c in CRITERIA if f"h_{c}" in r}).reset_index()
    item["h_mean"] = item[[f"h_{c}" for c in CRITERIA if f"h_{c}" in item]].mean(axis=1)
    res["teacher_means_by_arm"] = {
        a: {c: bootstrap_ci(g[f"h_{c}"].dropna().values)[0] for c in CRITERIA if f"h_{c}" in g}
        for a, g in item.groupby("arm")}
    item.to_csv(out / "human_item_means.csv", index=False)
    if len(qs) and "uid" in qs:
        j = item.merge(qs, on="uid", how="left", suffixes=("", "_q"))
        judge_cols = [f"judge_{c}" for c in CRITERIA if f"judge_{c}" in j]
        if judge_cols:
            j["judge_mean"] = j[judge_cols].astype(float).mean(axis=1)
            res["judge_vs_teacher_spearman"] = {
                c: spearman(j[f"judge_{c}"], j[f"h_{c}"]) for c in CRITERIA if f"judge_{c}" in j and f"h_{c}" in j}
            res["judge_vs_teacher_spearman"]["mean_of_criteria"] = spearman(j["judge_mean"], j["h_mean"])
        if "grounded" in j and "h_correctness" in j:
            teacher_ok = [None if pd.isna(v) else bool(v >= 4) for v in j["h_correctness"]]
            judge_ok = [None if pd.isna(v) else bool(v) for v in j["grounded"]]
            res["grounded_vs_teacher_correct_kappa"] = cohen_kappa(judge_ok, teacher_ok)
        j.to_csv(out / "judge_vs_teacher.csv", index=False)
        _scatter(j, out / "fig_judge_vs_teacher.png")
    return res


# ---------------------------------------------------------------- figures
def _style(ax) -> None:
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _bars(ex: pd.DataFrame, arms: list[str], path: Path) -> None:
    cols = [(c, l) for c, l, b in QUALITY if b and c in ex and not ex[c].isna().all()
            and not c.startswith("judge_") and not c.startswith("recall") and c != "mrr"]
    if not cols:
        return
    fig, ax = plt.subplots(figsize=(max(6, 1.4 * len(cols) * max(1, len(arms)) / 2), 4.2), dpi=200)
    width = 0.8 / max(1, len(arms))
    x = np.arange(len(cols))
    for i, a in enumerate(arms):
        means, err = [], [[], []]
        for c, _ in cols:
            m, lo, hi = bootstrap_ci(arm_values(ex, c, a))
            means.append(m)
            err[0].append(0 if math.isnan(lo) else m - lo)
            err[1].append(0 if math.isnan(hi) else hi - m)
        ax.bar(x + (i - (len(arms) - 1) / 2) * width, means, width * 0.92, yerr=err, label=a,
               color=PALETTE[i % len(PALETTE)], edgecolor="white", linewidth=1,
               error_kw={"elinewidth": 1, "ecolor": INK2, "capsize": 2})
    ax.set_xticks(x, [l for _, l in cols], rotation=15, ha="right", color=INK)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Mean over documents (95% CI)", color=INK2, fontsize=9)
    _style(ax)
    ax.legend(frameon=False, fontsize=9, ncol=min(len(arms), 4), loc="upper center", bbox_to_anchor=(0.5, 1.12))
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _latency(ex: pd.DataFrame, arms: list[str], path: Path) -> None:
    data = [ex.loc[(ex.arm == a) & ex.total_s.notna(), "total_s"].astype(float).values for a in arms]
    if not any(len(d) for d in data):
        return
    fig, ax = plt.subplots(figsize=(1.3 * len(arms) + 2.5, 3.6), dpi=200)
    bp = ax.boxplot(data, patch_artist=True, widths=0.5, medianprops={"color": INK, "linewidth": 1.5},
                    whiskerprops={"color": INK2}, capprops={"color": INK2}, flierprops={"markersize": 3})
    for i, b in enumerate(bp["boxes"]):
        b.set_facecolor(PALETTE[i % len(PALETTE)])
        b.set_alpha(0.85)
        b.set_edgecolor(INK2)
    ax.set_xticks(range(1, len(arms) + 1), arms)
    ax.set_ylabel("Time per exam (s)", color=INK2, fontsize=9)
    _style(ax)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _scatter(j: pd.DataFrame, path: Path) -> None:
    d = j[["judge_mean", "h_mean"]].dropna() if "judge_mean" in j else pd.DataFrame()
    if len(d) < 3:
        return
    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(4.2, 4.0), dpi=200)
    ax.scatter(d.judge_mean + rng.uniform(-0.06, 0.06, len(d)), d.h_mean, s=18, color=PALETTE[0],
               edgecolor="white", linewidth=0.6)
    ax.plot([1, 5], [1, 5], color=INK2, linewidth=1, linestyle="--")
    ax.set_xlim(0.8, 5.2)
    ax.set_ylim(0.8, 5.2)
    ax.set_xlabel("LLM judge (mean of 4 criteria)", color=INK2, fontsize=9)
    ax.set_ylabel("Teachers (mean of raters and criteria)", color=INK2, fontsize=9)
    _style(ax)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def analyze(run_specs: list[str], name: str, compare_pairs: list[tuple[str, str]] | None = None,
            ratings_csv: str | None = None, out_root: str = "analysis") -> Path:
    ex, qs = load_runs(run_specs)
    out = resolve(out_root) / name
    out.mkdir(parents=True, exist_ok=True)
    arms = list(dict.fromkeys(ex["arm"]))
    status = ex.groupby(["arm", "status"]).size().unstack(fill_value=0)
    infra = ex["status"].eq("error")
    if infra.any():
        print(f"[analyze] excluding {int(infra.sum())} exams with status=error (infrastructure) - "
              f"re-run them with --resume")
    ex_q = ex[~infra].copy()
    for col in ("format_compliant", "valid_json", "count_ok"):
        if col in ex_q:
            ex_q[col] = ex_q[col].map({True: 1.0, False: 0.0, "True": 1.0, "False": 0.0}).astype(float)

    at = arm_table(ex_q, arms)
    ct = cost_table(ex_q, arms)
    at.to_csv(out / "quality_by_arm.csv", index=False)
    ct.to_csv(out / "cost_by_arm.csv", index=False)
    status.to_csv(out / "status_by_arm.csv")
    comps = {}
    for a, b in compare_pairs or []:
        df = compare(ex_q, a, b)
        df.to_csv(out / f"compare_{a}_vs_{b}.csv", index=False)
        comps[(a, b)] = df
    human = human_analysis(ratings_csv, qs, out) if ratings_csv else None
    _bars(ex_q, arms, out / "fig_quality_by_arm.png")
    _latency(ex_q, arms, out / "fig_latency_by_arm.png")
    _write_summary(out, arms, status, at, ct, comps, human)
    print(f"[analyze] wrote {out}")
    return out


def _fmt(v, nd=3) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    return f"{v:.{nd}f}" if isinstance(v, (float, np.floating)) else str(v)


def _write_summary(out, arms, status, at, ct, comps, human) -> None:
    L = [f"# Analysis: {out.name}", "", "Documents are the unit of analysis: each metric is averaged over seeds "
         "and questions per document, then bootstrapped over documents (10,000 resamples, 95% CI).", "",
         "## Exam outcomes", "", status.to_markdown(), "", "## Quality by arm", ""]
    head = ["Metric"] + [f"{a} (95% CI)" for a in arms]
    L += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for _, r in at.iterrows():
        cells = [r["metric"]] + [f"{_fmt(r.get(a))} {r.get(f'{a} CI', '')}".strip() for a in arms]
        L.append("| " + " | ".join(cells) + " |")
    L += ["", "## Cost", "", ct.to_markdown(index=False, floatfmt=".1f") if len(ct) else "–", ""]
    for (a, b), df in comps.items():
        L += [f"## {a} vs {b} (paired Wilcoxon over documents, Holm-corrected)", ""]
        if len(df):
            cols = ["metric", "n_pairs", "mean_a", "mean_b", "mean_diff", "r_rb", "p", "p_holm", "better"]
            L += [df[cols].to_markdown(index=False, floatfmt=".4f"), ""]
        else:
            L += ["No paired documents.", ""]
    if human:
        L += ["## Teacher ratings", "", f"{human['n_ratings']} ratings, {human['n_items']} items, raters: "
              f"{', '.join(human['raters'])}", "", "Krippendorff's alpha: " +
              ", ".join(f"{k} = {_fmt(v)}" for k, v in human["krippendorff_alpha"].items()), ""]
        for a, m in human["teacher_means_by_arm"].items():
            L.append(f"- {a}: " + ", ".join(f"{k} {_fmt(v, 2)}" for k, v in m.items()))
        if "judge_vs_teacher_spearman" in human:
            L += ["", "Judge vs teachers (Spearman): " + ", ".join(
                f"{k} ρ = {_fmt(v['rho'])} (n={v['n']})" for k, v in human["judge_vs_teacher_spearman"].items())]
        if "grounded_vs_teacher_correct_kappa" in human:
            L.append(f"Cohen's κ, judge 'grounded' vs teacher correctness ≥ 4: "
                     f"{_fmt(human['grounded_vs_teacher_correct_kappa'])}")
        (out / "human.json").write_text(json.dumps(human, indent=2, ensure_ascii=False, default=str), "utf-8")
    (out / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
