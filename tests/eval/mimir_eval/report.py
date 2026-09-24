"""`report`: TDK-ready Hungarian figures and results text from the scored runs.

    python -m mimir_eval report                  -> report/  (latest run of every arm)
    python -m mimir_eval report --name pilot     -> report/pilot/

Writes, in Hungarian:
  tabla1_osszesito      ranked comparison table with the winner (and best local method) marked
  tabla2_gyoztes_vs_alap winner vs baseline, measure by measure, with the differences
  abra1_modszerek       how the methods work (diagram)
  abra2_rangsor         quality index per method, best highlighted, 95% CI
  abra3_mutatok         every quality measure per method (table-like heat map)
  abra4_minoseg_koltseg quality vs time per exam (what each gain costs)
  abra5_komponensek     E0 -> E1 -> E2 -> E3: what each added component contributes
  abra6_darabolas       chunking variants (if E5a-c were run)
  tabla3_egyetertes     judge-teacher agreement: Krippendorff α, Spearman ρ, Cohen κ (needs ratings.csv)
  tabla4_szignifikancia paired Wilcoxon for E1-E0, E2-E1, E3-E2, E4-E0, Holm p, rank-biserial r
  tabla5_nyelvek        Hungarian vs English per arm (+ abra7_nyelvek)
  tabla6_adatkeszlet    documents, gold questions, lengths and licence per source (+ adatkeszlet.csv)
  peldak.md             one good and one bad question per arm with the judge's reasoning
  eredmenyek.md         a results-chapter draft with the numbers filled in
  eredmenyek_tabla.csv  the main table
Every figure is saved as PNG (300 dpi) and PDF (vector) for Word or LaTeX.
"""
from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

from .config import resolve  # noqa: E402
from .rubric import CRITERIA  # noqa: E402
from .stats import bootstrap_ci, holm, paired_wilcoxon  # noqa: E402

ARM_HU = {
    "E0": ("Alapmódszer", "naiv RAG: 3 részlet, egy hívásban 10 kérdés"),
    "E1": ("Tervezés", "fogalmak megtervezése, kérdésenként külön írás"),
    "E2": ("Tervezés + ellenőrzés", "minden kérdés ellenőrzése, hiba esetén újraírás"),
    "E2f": ("Ellenőrzés vak teszt nélkül", "E2 a vak megoldási próba nélkül"),
    "E2h": ("Ellenőrzés + hibrid keresés", "E2 kulcsszavas és jelentés alapú kereséssel"),
    "E3": ("Ellenőrzés + fogalomgráf", "E2 kiegészítve a dokumentum fogalomtérképével"),
    "E4": ("Alapmódszer, szervermodell", "E0 az egyetemi szerver nagy modelljén"),
    "E4b": ("Ellenőrzés, szervermodell", "E2 az egyetemi szerver nagy modelljén"),
    "E5a": ("Régi darabolás", "E0 a javítás előtti RuneCarverrel"),
    "E5b": ("Szórás alapú darabolás", "E0, vágás a téma-váltás szórása alapján"),
    "E5c": ("Fix darabolás", "E0, 800 karakteres darabok"),
}
METRICS_HU = [  # column, label; all "higher is better", 0..1
    ("format_compliant", "Formai megfelelés"),
    ("grounding_rate", "Forrással igazolt válasz"),
    ("blind_answerability", "Vakon megoldható"),
    ("distractor_validity", "Jó disztraktorok"),
]
EXTRA_HU = [("meta_reference_rate", "„A szöveg szerint” arány (kisebb a jobb)"),
            ("coverage", "Lefedettség"), ("recall@3", "Keresési találat @3")]
BEST, OTHER, INK, INK2, GRID = "#2a78d6", "#b9b8b2", "#1b1b19", "#5b5a55", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})


def hu(v: float, nd: int = 2) -> str:
    """Hungarian decimal comma."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    return f"{v:.{nd}f}".replace(".", ",")


def pct(v: float) -> str:
    return "–" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{round(v * 100)}%"


def az(word: str) -> str:
    """Hungarian definite article: 'az E4', 'a Tervezés'."""
    return "az" if word[:1].upper() in "AEIOUÁÉÍÓÖŐÚÜŰ5" or word.startswith("1") else "a"


def label(arm: str) -> str:
    return f"{arm} – {ARM_HU.get(arm, (arm, ''))[0]}"


# ---------------------------------------------------------------- data
def load_latest(results_root: Path, arms: list[str] | None) -> pd.DataFrame:
    frames = []
    latest: dict[str, Path] = {}
    for rd in sorted(p for p in results_root.iterdir() if (p / "exam_metrics.csv").exists()):
        cfg = json.loads((rd / "run.json").read_text(encoding="utf-8")).get("config", {})
        latest[cfg.get("name", rd.name)] = rd      # sorted by name+timestamp: last one wins
    for arm, rd in latest.items():
        if arms and arm not in arms:
            continue
        df = pd.read_csv(rd / "exam_metrics.csv")
        df["arm"] = arm
        df["run_dir"] = rd.name
        frames.append(df)
    if not frames:
        raise SystemExit(f"no scored runs under {results_root} (run `score` first)")
    ex = pd.concat(frames, ignore_index=True)
    ex = ex[ex["status"] != "error"].copy()          # infrastructure failures are not results
    for c in ("format_compliant", "valid_json", "count_ok"):
        if c in ex:
            ex[c] = ex[c].map({True: 1.0, False: 0.0, "True": 1.0, "False": 0.0}).astype(float)
    return ex


def quality_metrics(ex: pd.DataFrame) -> list[tuple[str, str]]:
    """The index uses only measures every arm has, so the comparison stays fair."""
    out = []
    for col, lab in METRICS_HU:
        if col in ex and ex.groupby("arm")[col].apply(lambda s: s.notna().any()).all():
            out.append((col, lab))
    return out


def add_index(ex: pd.DataFrame, metrics: list[tuple[str, str]]) -> pd.DataFrame:
    cols = [c for c, _ in metrics]
    ex = ex.copy()
    vals = ex[cols].apply(pd.to_numeric, errors="coerce")
    # a failed exam (no questions) keeps its 0 format score and nothing else -> index 0
    ex["quality_index"] = vals.mean(axis=1, skipna=True)
    return ex


def per_doc(ex: pd.DataFrame, col: str, arm: str) -> pd.Series:
    sub = ex[ex.arm == arm]
    return sub.groupby("doc_id")[col].apply(lambda s: pd.to_numeric(s, errors="coerce").mean()).dropna()


def summarize(ex: pd.DataFrame, metrics) -> pd.DataFrame:
    rows = []
    for arm in ex["arm"].unique():
        d = per_doc(ex, "quality_index", arm)
        m, lo, hi = bootstrap_ci(d.values)
        sub = ex[ex.arm == arm]
        models = sub["model_used"].astype(str) if "model_used" in sub else pd.Series(dtype=str)
        row = {"arm": arm, "nev": ARM_HU.get(arm, (arm, ""))[0], "qi": m,
               "helyi": not (models.str.startswith("genai").any() or arm in ("E4", "E4b")), "ci_lo": lo, "ci_hi": hi,
               "n_docs": len(d), "n_exams": len(sub),
               "ido_median_s": float(pd.to_numeric(sub["total_s"], errors="coerce").median()),
               "llm_hivas_median": float(pd.to_numeric(sub.get("llm_calls"), errors="coerce").median())
               if "llm_calls" in sub else math.nan}
        for col, _ in metrics + EXTRA_HU:
            row[col] = per_doc(ex, col, arm).mean() if col in ex else math.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values("qi", ascending=False).reset_index(drop=True)


def significance(ex: pd.DataFrame, best: str, others: list[str]) -> pd.DataFrame:
    rows = []
    b = per_doc(ex, "quality_index", best)
    for o in others:
        s = per_doc(ex, "quality_index", o)
        common = b.index.intersection(s.index)
        r = paired_wilcoxon(s.loc[common].values, b.loc[common].values)
        rows.append({"arm": o, **r})
    df = pd.DataFrame(rows)
    if len(df):
        df["p_holm"] = holm(df["p"].tolist())
    return df


# ---------------------------------------------------------------- figures
PILOT = {"on": False}


def _save(fig, out: Path, name: str, pilot_label: bool = True) -> None:
    if pilot_label and PILOT["on"] and name != "abra1_modszerek":
        fig.text(0.995, 0.995, "PILOT – kevés dokumentum, nem végleges", ha="right", va="top", fontsize=7,
                 color="#b3261e")
    fig.savefig(out / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def _comma(ax, axis: str = "y") -> None:
    """Hungarian decimal comma on a numeric axis."""
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(f)


def _box(ax, x, y, w, h, text, color="#ffffff", edge=INK2, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=color, ec=edge, lw=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8.5, color=INK,
            fontweight="bold" if bold else "normal", wrap=True)


def _arrow(ax, x1, y1, x2, y2, style="-|>", color=INK2, rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=10, color=color, lw=1,
                                 connectionstyle=f"arc3,rad={rad}"))


def fig_methods(out: Path) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    ax.set_xlim(-0.15, 10.4)
    ax.set_ylim(-0.1, 4.6)
    ax.axis("off")
    # naive
    ax.text(0, 4.35, "E0 – Alapmódszer (naiv RAG)", fontsize=10, fontweight="bold", color=INK)
    xs = [0, 2.1, 4.2, 6.5, 8.6]
    labels = ["Dokumentum", "Darabolás\n(RuneCarver)", "3 legközelebbi\nrészlet", "1 LLM-hívás:\nmind a 10 kérdés",
              "Vizsga"]
    for i, (x, t) in enumerate(zip(xs, labels)):
        _box(ax, x, 3.35, 1.55 if i != 3 else 1.8, 0.75, t)
        if i:
            _arrow(ax, xs[i - 1] + (1.55 if i - 1 != 3 else 1.8), 3.72, x, 3.72)
    # blueprint
    ax.text(0, 2.55, "E1–E3 – Tervezett, lépésenkénti módszer", fontsize=10, fontweight="bold", color=INK)
    _box(ax, 0, 1.35, 1.35, 0.75, "Dokumentum\n+ darabolás")
    _box(ax, 1.7, 1.35, 1.45, 0.75, "Fogalomgráf\n(csak E3)", color="#eef4fc", edge=BEST)
    _box(ax, 3.5, 1.35, 1.35, 0.75, "Tervező:\nfogalom, típus,\nBloom-szint")
    ax.add_patch(FancyBboxPatch((5.15, 0.25), 3.25, 2.05, boxstyle="round,pad=0.02,rounding_size=0.1",
                                fc="none", ec=GRID, lw=1, ls="--"))
    ax.text(5.25, 2.12, "minden kérdésre külön", fontsize=7.5, color=INK2)
    _box(ax, 5.3, 1.35, 1.35, 0.6, "Célzott\nkeresés")
    _box(ax, 6.9, 1.35, 1.35, 0.6, "1 kérdés\nforrással")
    _box(ax, 6.1, 0.4, 1.55, 0.6, "Ellenőrzés\n(E2, E3)", color="#eef4fc", edge=BEST)
    _box(ax, 8.65, 1.35, 1.3, 0.75, "Összeállítás\n→ Vizsga")
    _arrow(ax, 1.35, 1.72, 1.7, 1.72)
    _arrow(ax, 3.15, 1.72, 3.5, 1.72)
    _arrow(ax, 4.85, 1.72, 5.3, 1.65)
    _arrow(ax, 6.65, 1.65, 6.9, 1.65)
    _arrow(ax, 7.6, 1.35, 7.25, 1.0)
    _arrow(ax, 6.3, 1.0, 5.95, 1.35, color=BEST)
    ax.text(5.2, 1.08, "hiba →\nújraírás", fontsize=7, color=BEST, ha="left")
    _arrow(ax, 8.25, 1.65, 8.65, 1.72)
    ax.text(0, 0.05, "Kék: a kísérletben ki- és bekapcsolt részek. E2f: vak teszt nélkül; E2h: hibrid keresés; "
            "E4/E4b: ugyanez az egyetemi szervermodellel.", fontsize=7.5, color=INK2)
    _save(fig, out, "abra1_modszerek")


def fig_ranking(summary: pd.DataFrame, best: str, out: Path) -> None:
    s = summary.iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 0.42 * len(s) + 1.1))
    y = np.arange(len(s))
    for i, r in enumerate(s.itertuples()):
        c = BEST if r.arm == best else OTHER
        if not math.isnan(r.ci_lo):
            ax.plot([r.ci_lo, r.ci_hi], [i, i], color=c, lw=2, solid_capstyle="round")
        ax.plot(r.qi, i, "o", color=c, ms=8, mec="white", mew=1.5)
        ax.text(1.02, i, hu(r.qi), va="center", fontsize=8.5, color=INK if r.arm == best else INK2,
                fontweight="bold" if r.arm == best else "normal", transform=ax.get_yaxis_transform())
    ax.set_yticks(y, [label(a) for a in s["arm"]])
    for t, a in zip(ax.get_yticklabels(), s["arm"]):
        if a == best:
            t.set_fontweight("bold")
            t.set_color(INK)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Minőségi index (0–1), dokumentumonkénti átlag, 95%-os konfidenciaintervallum")
    _comma(ax, "x")
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    _save(fig, out, "abra2_rangsor")


def fig_metrics(summary: pd.DataFrame, metrics, best: str, out: Path) -> None:
    import textwrap
    cols = [c for c, _ in metrics] + [c for c, _ in EXTRA_HU if c in summary and summary[c].notna().any()]
    labs = [lab for c, lab in metrics + EXTRA_HU if c in cols]
    data = summary[cols].to_numpy(dtype=float)
    shown = data.copy()
    if "meta_reference_rate" in cols:        # colour "lower is better" the right way round
        shown[:, cols.index("meta_reference_rate")] = 1 - shown[:, cols.index("meta_reference_rate")]
    wrapped = ["\n".join(textwrap.wrap(l, 13)) for l in labs]
    head_lines = max(w.count("\n") + 1 for w in wrapped)
    name_w = max(len(label(a)) for a in summary["arm"]) * 0.068 + 0.3
    fig_w = name_w + 1.15 * len(cols)
    fig_h = 0.36 * len(summary) + 0.2 * head_lines + 0.5
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.imshow(np.nan_to_num(shown, nan=0.0), cmap="Blues", vmin=0, vmax=1.25, aspect="auto")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            ax.text(j, i, pct(v), ha="center", va="center", fontsize=8.5,
                    color="white" if not math.isnan(v) and shown[i, j] > 0.72 else INK)
    ax.xaxis.tick_top()
    ax.set_xticks(range(len(cols)), wrapped, fontsize=8, linespacing=1.1)
    ax.set_yticks(range(len(summary)), [label(a) for a in summary["arm"]], fontsize=8.5)
    for t, a in zip(ax.get_yticklabels(), summary["arm"]):
        if a == best:
            t.set_fontweight("bold")
            t.set_color(INK)
    ax.set_xticks(np.arange(-0.5, len(cols), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(summary), 1), minor=True)
    ax.grid(which="minor", color="white", lw=2)
    ax.tick_params(which="both", length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    fig.tight_layout()
    _save(fig, out, "abra3_mutatok")


def fig_cost(summary: pd.DataFrame, best: str, out: Path) -> None:
    s = summary.dropna(subset=["ido_median_s"])
    if s.empty:
        return
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    placed: list[tuple[float, float]] = []
    offsets = [(6, 4), (6, -11), (-22, 4), (-22, -11), (6, 14), (-22, 14)]
    for r in s.sort_values("qi", ascending=False).itertuples():
        x, y = r.ido_median_s / 60, r.qi
        c = BEST if r.arm == best else OTHER
        ax.scatter(x, y, s=60, color=c, edgecolor="white", lw=1.2, zorder=3)
        near = sum(1 for px, py in placed if abs(math.log10(x) - math.log10(px)) < 0.12 and abs(y - py) < 0.08)
        placed.append((x, y))
        ax.annotate(r.arm, (x, y), xytext=offsets[near % len(offsets)], textcoords="offset points",
                    fontsize=8.5, color=INK if r.arm == best else INK2,
                    fontweight="bold" if r.arm == best else "normal")
    ax.set_xscale("log")
    ticks = [t for t in (0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 60) if s.ido_median_s.min() / 60 / 1.5 <= t <= s.ido_median_s.max() / 60 * 1.5]
    ax.set_xticks(ticks, [hu(t, 2).rstrip("0").rstrip(",") for t in ticks])
    ax.minorticks_off()
    ax.set_xlabel("Idő egy 10 kérdéses vizsgára (perc, medián, log skála)")
    ax.set_ylabel("Minőségi index (0–1)")
    ax.set_ylim(0, 1.05)
    _comma(ax)
    ax.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.text(0.99, 0.02, "fent-balra: jobb és gyorsabb", transform=ax.transAxes, ha="right", fontsize=7.5,
            color=INK2)
    _save(fig, out, "abra4_minoseg_koltseg")


def fig_components(summary: pd.DataFrame, out: Path) -> list[tuple[str, float, float]]:
    chain = [a for a in ("E0", "E1", "E2", "E3") if a in set(summary["arm"])]
    if len(chain) < 2:
        return []
    idx = summary.set_index("arm")["qi"]
    steps = [(chain[0], idx[chain[0]], 0.0)] + [(a, idx[a], idx[a] - idx[p]) for p, a in zip(chain, chain[1:])]
    names = {"E0": "Alapmódszer", "E1": "+ tervezés", "E2": "+ ellenőrzés", "E3": "+ fogalomgráf"}
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    prev = 0.0
    for i, (a, v, d) in enumerate(steps):
        if i == 0:
            ax.bar(i, v, color=OTHER, width=0.6)
        else:
            lo, hi = sorted((prev, v))
            ax.bar(i, hi - lo, bottom=lo, width=0.6, color=BEST if d >= 0 else "#d9534f")
            ax.plot([i - 1 + 0.3, i - 0.3], [prev, prev], color=INK2, lw=0.8, ls=":")
        top = v if i == 0 else max(prev, v)
        ax.text(i, top + 0.02, hu(v) + ("" if i == 0 else f"\n({'+' if d >= 0 else ''}{hu(d)})"), ha="center",
                va="bottom", fontsize=8, color=INK, linespacing=1.1)
        prev = v
    ax.set_xticks(range(len(steps)), [f"{a}\n{names[a]}" for a, _, _ in steps])
    ax.set_ylim(0, 1.2)
    ax.set_ylabel("Minőségi index (0–1)")
    _comma(ax)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    _save(fig, out, "abra5_komponensek")
    return steps


def fig_chunking(summary: pd.DataFrame, out: Path) -> bool:
    arms = [a for a in ("E5a", "E0", "E5b", "E5c") if a in set(summary["arm"])]
    if len(arms) < 2:
        return False
    s = summary.set_index("arm").loc[arms]
    cols = [("qi", "Minőségi index (0–1)")] + ([("recall@3", "Keresési találat @3 (0–1)")]
                                                if "recall@3" in s and s["recall@3"].notna().any() else [])
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    w = 0.8 / len(cols)
    for k, (c, lab) in enumerate(cols):
        vals = s[c].astype(float).values
        xs = np.arange(len(arms)) + (k - (len(cols) - 1) / 2) * w
        ax.bar(xs, vals, w * 0.92, color=[BEST, "#9fc3ee"][k], label=lab)
        for x, v in zip(xs, vals):
            ax.text(x, (0 if math.isnan(v) else v) + 0.02, hu(v), ha="center", fontsize=7.5, color=INK2)
    ax.set_xticks(range(len(arms)), [f"{a}\n{ARM_HU[a][0]}" for a in arms], fontsize=8)
    ax.set_ylim(0, 1.12)
    _comma(ax)
    ax.legend(frameon=False, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=len(cols))
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    _save(fig, out, "abra6_darabolas")
    return True


def _draw_table(header: list[str], rows: list[list[str]], out: Path, name: str, highlight: set[int],
                colors: dict | None = None, left_cols: set[int] = frozenset({1}), title: str = "") -> None:
    """A clean table as a figure: column widths from the text, highlighted rows, no overlaps."""
    import textwrap
    colors = colors or {}
    head = ["\n".join(textwrap.wrap(h, 14)) or h for h in header]
    cw = [max([len(line) for line in head[j].split("\n")] + [len(r[j]) for r in rows]) * 0.075 + 0.28
          for j in range(len(header))]
    head_h = 0.2 * max(h.count("\n") + 1 for h in head) + 0.16
    row_h = 0.3
    note = PILOT["on"]
    top = (0.35 if title else 0.05) + (0.22 if note else 0.0)
    W, H = sum(cw), head_h + row_h * len(rows) + top
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    y0 = top - 0.05 if title else top
    if title:
        ax.text(0.05, 0.15, title, fontsize=9.5, fontweight="bold", color=INK, va="center")
    if note:   # own line under the title, so it can never collide with it
        ax.text(0.05, 0.15 + (0.24 if title else 0.0), "PILOT – kevés dokumentum, nem végleges",
                fontsize=7, color="#b3261e", va="center")
    ax.add_patch(plt.Rectangle((0, y0), W, head_h, color="#efeeea", lw=0))
    x = 0
    for j, h in enumerate(head):
        ax.text(x + (0.08 if j in left_cols else cw[j] / 2), y0 + head_h / 2, h, ha="left" if j in left_cols else "center",
                va="center", fontsize=8, fontweight="bold", color=INK, linespacing=1.1)
        x += cw[j]
    for i, r in enumerate(rows):
        y = y0 + head_h + i * row_h
        if i in highlight:
            ax.add_patch(plt.Rectangle((0, y), W, row_h, color="#e3eefb", lw=0))
        ax.plot([0, W], [y + row_h, y + row_h], color=GRID, lw=0.6)
        x = 0
        for j, c in enumerate(r):
            ax.text(x + (0.08 if j in left_cols else cw[j] / 2), y + row_h / 2, c,
                    ha="left" if j in left_cols else "center", va="center", fontsize=8,
                    color=colors.get((i, j), INK), fontweight="bold" if i in highlight else "normal")
            x += cw[j]
    _save(fig, out, name, pilot_label=False)


def table_rank(summary: pd.DataFrame, metrics, best: str, best_local: str | None, out: Path) -> list[list[str]]:
    header = ["Hely", "Módszer", "Minőségi index"] + [lab for _, lab in metrics] + \
             ["Idő / vizsga (perc)", "LLM-hívás / vizsga", "Eredmény"]
    rows, hl = [], set()
    for i, r in enumerate(summary.itertuples()):
        verdict = "★ Győztes" if r.arm == best else ("Legjobb helyi" if r.arm == best_local else "")
        if r.arm == best and best == best_local:
            verdict = "★ Győztes (helyi is)"
        if r.arm in (best, best_local):
            hl.add(i)
        rows.append([f"{i + 1}.", label(r.arm), hu(r.qi)] + [pct(getattr(r, c) if hasattr(r, c) else r._asdict()[c])
                                                               for c, _ in metrics] +
                    [hu(r.ido_median_s / 60, 1), hu(r.llm_hivas_median, 0), verdict])
    _draw_table(header, rows, out, "tabla1_osszesito", hl, title="A módszerek összesített rangsora")
    return [header] + rows


def table_winner(summary: pd.DataFrame, metrics, best: str, out: Path) -> tuple[str, list[list[str]]] | None:
    s = summary.set_index("arm")
    base = "E0" if "E0" in s.index and best != "E0" else (summary.iloc[1]["arm"] if len(summary) > 1 else None)
    if base is None:
        return None
    header = ["Mutató", f"{base} – {ARM_HU.get(base, (base, ''))[0]}", f"{best} – {ARM_HU.get(best, (best, ''))[0]}",
              "Különbség"]
    items = [("qi", "Minőségi index", "num")] + [(c, lab, "pct") for c, lab in metrics] + \
            [("ido_median_s", "Idő / vizsga (perc)", "time"), ("llm_hivas_median", "LLM-hívás / vizsga", "calls")]
    rows, colors = [], {}
    for i, (c, lab, kind) in enumerate(items):
        a, b = float(s.loc[base, c]), float(s.loc[best, c])
        if kind == "num":
            av, bv, d, good = hu(a), hu(b), f"{'+' if b - a >= 0 else ''}{hu(b - a)}", b >= a
        elif kind == "pct":
            av, bv, good = pct(a), pct(b), b >= a
            d = "–" if math.isnan(a) or math.isnan(b) else f"{'+' if b - a >= 0 else ''}{round((b - a) * 100)} %-pont"
        elif kind == "time":
            av, bv = hu(a / 60, 1), hu(b / 60, 1)
            ratio = b / a if a else math.nan
            d, good = (f"{hu(ratio, 1)}× lassabb" if ratio >= 1 else f"{hu(1 / ratio, 1)}× gyorsabb"), ratio <= 1
        else:
            av, bv, d, good = hu(a, 0), hu(b, 0), (f"{hu(b / a, 0)}×" if a else "–"), b <= a
        colors[(i, 3)] = "#1f7a3a" if good else "#b3261e"
        rows.append([lab, av, bv, d])
    _draw_table(header, rows, out, "tabla2_gyoztes_vs_alap", set(), colors, left_cols={0},
                title=f"A győztes ({best}) az alapmódszerhez ({base}) képest")
    return base, [header] + rows


def md_table(rows: list[list[str]]) -> list[str]:
    head, body = rows[0], rows[1:]
    return ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(r) + " |" for r in body]


# ---------------------------------------------------------------- TDK sections (AI-13 - AI-17)
KEY_PAIRS = [("E1", "E0"), ("E2", "E1"), ("E3", "E2"), ("E4", "E0")]   # (new, reference): what each step adds
CRIT_HU = {"correctness": "Helyesség", "clarity": "Érthetőség", "distractor_quality": "Disztraktorok",
           "bloom_fit": "Szintillesztés", "would_use": "Használná (igen/nem)"}
LANG_HU = {"hu": "magyar", "en": "angol"}
LENGTHS = [("short", "rövid"), ("medium", "közepes"), ("long", "hosszú")]


def load_questions(results_root: Path, run_dirs) -> pd.DataFrame:
    """questions.jsonl of the given run folders (arm taken from each row)."""
    from .util import read_jsonl
    rows = []
    for rd in sorted(set(run_dirs)):
        p = results_root / rd / "questions.jsonl"
        if p.exists():
            rows += read_jsonl(p)
    return pd.DataFrame(rows)


def table_significance(ex: pd.DataFrame, out: Path) -> tuple[pd.DataFrame, list[list[str]]] | None:
    """AI-14: paired Wilcoxon over documents for the key steps, Holm-corrected over this family."""
    arms = set(ex["arm"])
    rows = []
    for new, ref in KEY_PAIRS:
        if new in arms and ref in arms:
            a, b = per_doc(ex, "quality_index", ref), per_doc(ex, "quality_index", new)
            common = a.index.intersection(b.index)
            rows.append({"new": new, "ref": ref, **paired_wilcoxon(a.loc[common].values, b.loc[common].values)})
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df["p_holm"] = holm(df["p"].tolist())
    header = ["Összevetés", "Dokumentum (n)", "Referencia", "Új módszer", "Különbség", "Hatásméret (r)",
              "p", "p (Holm)", "Szignifikáns"]
    body, colors = [], {}
    for i, r in enumerate(df.itertuples()):
        sig = not math.isnan(r.p_holm) and r.p_holm < 0.05
        verdict = "igen" if sig else ("nem (n < 6)" if r.n_pairs < 6 else "nem")
        body.append([f"{r.new} vs {r.ref}", str(r.n_pairs), hu(r.mean_a), hu(r.mean_b),
                     ("–" if math.isnan(r.mean_diff) else f"{'+' if r.mean_diff >= 0 else ''}{hu(r.mean_diff)}"),
                     hu(r.r_rb), hu(r.p, 3), hu(r.p_holm, 3), verdict])
        colors[(i, 8)] = "#1f7a3a" if sig else INK2
    _draw_table(header, body, out, "tabla4_szignifikancia", set(), colors, left_cols={0},
                title="Páros Wilcoxon-próbák a minőségi indexen (dokumentumonként)")
    df.to_csv(out / "szignifikancia.csv", index=False, encoding="utf-8-sig")
    return df, [header] + body


def table_languages(ex: pd.DataFrame, summary: pd.DataFrame, metrics, out: Path) -> list[list[str]] | None:
    """AI-15: quality index and every measure per language, per arm (descriptive: different documents)."""
    if "language" not in ex:
        return None
    langs = [lang for lang in ("hu", "en") if lang in set(ex["language"].dropna())]
    if len(langs) < 2:
        return None
    header = ["Módszer"] + [f"Index – {LANG_HU[lang]} (n)" for lang in langs] + ["Különbség (magyar − angol)"] + \
             [f"{lab} (magyar / angol)" for _, lab in metrics]
    body, vals = [], {}
    for arm in summary["arm"]:
        sub = ex[ex.arm == arm]
        cells, qi = [label(arm)], {}
        for lang in langs:
            d = per_doc(sub[sub.language == lang], "quality_index", arm)
            qi[lang] = d.mean() if len(d) else math.nan
            cells.append(f"{hu(qi[lang])} ({len(d)})")
        diff = qi["hu"] - qi["en"]
        cells.append("–" if math.isnan(diff) else f"{'+' if diff >= 0 else ''}{hu(diff)}")
        for col, _ in metrics:
            cells.append(" / ".join(pct(per_doc(sub[sub.language == lang], col, arm).mean()) for lang in langs))
        body.append(cells)
        vals[arm] = qi
    _draw_table(header, body, out, "tabla5_nyelvek", set(), left_cols={0},
                title="Magyar és angol dokumentumok módszerenként")
    fig_languages(vals, langs, out)
    return [header] + body


def fig_languages(vals: dict, langs: list[str], out: Path) -> None:
    arms = list(vals)[::-1]
    fig, ax = plt.subplots(figsize=(6.6, 0.5 * len(arms) + 1.2))
    h = 0.38
    for k, (lang, c) in enumerate(zip(langs, (BEST, "#9fc3ee"))):
        ys = np.arange(len(arms)) + (k - 0.5) * h
        xs = [vals[a][lang] for a in arms]
        ax.barh(ys, np.nan_to_num(xs), h * 0.92, color=c, label=LANG_HU[lang])
        for y, x in zip(ys, xs):
            ax.text((0 if math.isnan(x) else x) + 0.01, y, hu(x), va="center", fontsize=7.5, color=INK2)
    ax.set_yticks(range(len(arms)), [label(a) for a in arms], fontsize=8.5)
    ax.set_xlim(0, 1.1)
    ax.set_xlabel("Minőségi index (0–1), dokumentumonkénti átlag")
    _comma(ax, "x")
    ax.legend(frameon=False, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    _save(fig, out, "abra7_nyelvek")


def _source_name(license_: str) -> str:
    """'CC-BY-4.0 (OpenStax via EduQG)' -> 'OpenStax via EduQG'; 'own' -> 'saját'."""
    if "(" in license_ and license_.endswith(")"):
        return license_[license_.index("(") + 1:-1]
    return "saját" if license_ in ("own", "") else license_


def table_dataset(ex: pd.DataFrame, results_root: Path, out: Path) -> tuple[dict, list[list[str]]] | None:
    """AI-16: documents, gold questions, language, length and licence per source (methods chapter)."""
    from .dataset import load_dataset
    run = ex["run_dir"].iloc[0]
    cfg = json.loads((results_root / run / "run.json").read_text(encoding="utf-8"))["config"]
    try:
        ds = load_dataset(cfg["dataset"])
    except (FileNotFoundError, KeyError) as e:
        print(f"[report] dataset table skipped: {e}")
        return None
    used = set(ex["doc_id"])
    docs = []
    for d in ds.documents:
        chars = d.extra.get("chars")
        if chars is None:
            try:
                chars = len(d.read_text())
            except (OSError, UnicodeDecodeError):
                chars = math.nan
        docs.append({"id": d.id, "forras": _source_name(d.license), "nyelv": d.language,
                     "hossz": d.extra.get("length", ""), "tema": d.subject, "karakter": chars,
                     "arany_kerdes": len(d.gold()), "licenc": d.license.split(" (")[0] or "–",
                     "kiertekelve": d.id in used})
    df = pd.DataFrame(docs)
    df.to_csv(out / "adatkeszlet.csv", index=False, encoding="utf-8-sig")
    header = ["Forrás", "Nyelv", "Dokumentum", "Rövid / közepes / hosszú", "Karakter (átlag)",
              "Karakter (min–max)", "Arany kérdés", "Licenc", "Kiértékelve"]
    body = []
    groups = list(df.groupby(["forras", "nyelv"], sort=False))
    for (src, lang), g in groups + [(("Összesen", "–"), df)]:
        lens = " / ".join(str(int((g["hossz"] == k).sum())) for k, _ in LENGTHS)
        c = pd.to_numeric(g["karakter"], errors="coerce")
        body.append([src, LANG_HU.get(lang, lang), str(len(g)), lens,
                     "–" if c.isna().all() else f"{c.mean():,.0f}".replace(",", " "),
                     "–" if c.isna().all() else f"{c.min():,.0f}–{c.max():,.0f}".replace(",", " "),
                     str(int(g["arany_kerdes"].sum())),
                     ", ".join(sorted(set(g["licenc"]))) if src != "Összesen" else "–",
                     str(int(g["kiertekelve"].sum()))])
    _draw_table(header, body, out, "tabla6_adatkeszlet", {len(body) - 1}, left_cols={0},
                title=f"Az értékelő adatkészlet ({ds.version})")
    info = {"version": ds.version, "n_docs": len(df), "n_used": int(df["kiertekelve"].sum()),
            "n_gold": int(df["arany_kerdes"].sum()),
            "by_lang": {lang: int((df["nyelv"] == lang).sum()) for lang in df["nyelv"].unique()}}
    return info, [header] + body


def _judge_mean(row) -> float:
    vals = [row.get(f"judge_{c}") for c in CRITERIA]
    vals = [float(v) for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
    return sum(vals) / len(vals) if vals else math.nan


def pick_examples(qs: pd.DataFrame) -> dict[str, dict[str, dict]]:
    """AI-17: per arm the best and the worst judged question. Good = grounded and not failed blind,
    highest mean rubric score; bad = not grounded (or failed blind) first, then lowest score."""
    out: dict[str, dict[str, dict]] = {}
    if qs.empty or "grounded" not in qs:
        return out
    for arm, g in qs.groupby("arm", sort=False):
        recs = [r for r in g.to_dict("records") if r.get("grounded") is not None
                and not (isinstance(r.get("grounded"), float) and math.isnan(r["grounded"]))]
        if not recs:
            continue
        for r in recs:
            r["_score"] = _judge_mean(r)
            b = r.get("blind_correct")
            r["_blind_fail"] = b is not None and not pd.isna(b) and not bool(b)
        s = lambda r: -1.0 if math.isnan(r["_score"]) else r["_score"]  # noqa: E731
        good = [r for r in recs if r["grounded"] and not r["_blind_fail"]]
        pick = {}
        if good:
            pick["jo"] = max(good, key=lambda r: (s(r), r["uid"]))
        bad_pool = [r for r in recs if r is not pick.get("jo")]
        if bad_pool:
            pick["rossz"] = min(bad_pool, key=lambda r: (bool(r["grounded"]) and not r["_blind_fail"], s(r), r["uid"]))
        out[arm] = pick
    return out


def _yes(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    return "igen" if bool(v) else "nem"


def write_examples(qs: pd.DataFrame, order: list[str], out: Path) -> int:
    ex = pick_examples(qs)
    if not ex:
        return 0
    L = ["# Példakérdések a hibaelemzéshez", "",
         "Módszerenként egy jó és egy rossz kérdés a független bíráló (LLM) értékelése alapján. Jó: a forrás "
         "igazolja a megjelölt választ, a vak megoldás nem hibázott, és a legmagasabb a négy szempont átlaga. Rossz: "
         "a forrás nem igazolja a választ (vagy a vak megoldó mást jelölt), azon belül a legalacsonyabb átlag.", ""]
    rows = []
    for arm in [a for a in order if a in ex]:
        L += [f"## {label(arm)}", ""]
        for kind, title in (("jo", "Jó példa"), ("rossz", "Rossz példa")):
            q = ex[arm].get(kind)
            if not q:
                continue
            L += [f"### {title} – `{q['doc_id']}`, seed {q['seed']}", "", f"**{q['text']}**", ""]
            for i, o in enumerate(q.get("options") or []):
                L.append(f"{'ABCDEFGH'[i]}. {o['text']}{' ✓' if o.get('correct') else ''}")
            scores = ", ".join(f"{CRIT_HU[c].lower()} {q.get(f'judge_{c}')}" for c in CRITERIA
                               if q.get(f"judge_{c}") is not None and not pd.isna(q.get(f"judge_{c}")))
            L += ["", f"- Forrással igazolt: {_yes(q.get('grounded'))}; vakon megoldva: {_yes(q.get('blind_correct'))}"
                  + (f"; pontszámok (1–5): {scores}" if scores else ""),
                  f"- A bíráló indoklása: {q.get('judge_rationale') or '–'}"]
            if q.get("key_evidence"):
                L.append(f"- Alátámasztó mondat: „{q['key_evidence']}”")
            L.append("")
            rows.append({"modszer": arm, "tipus": kind, "uid": q["uid"], "kerdes": q["text"],
                         "forrassal_igazolt": q.get("grounded"), "vakon_megoldva": q.get("blind_correct"),
                         "atlag_pont": q["_score"], "indoklas": q.get("judge_rationale")})
    (out / "peldak.md").write_text("\n".join(L), encoding="utf-8")
    pd.DataFrame(rows).to_csv(out / "peldak.csv", index=False, encoding="utf-8-sig")
    return len(rows)


def _alpha_hu(a: float) -> str:
    if math.isnan(a):
        return "–"
    return "megbízható" if a >= 0.8 else "elfogadható" if a >= 0.667 else "gyenge"


def _rho_hu(r: float) -> str:
    if math.isnan(r):
        return "–"
    if r < 0:
        return "negatív"
    return "erős" if r >= 0.7 else "közepes" if r >= 0.4 else "gyenge"


def _kappa_hu(k: float) -> str:   # Landis & Koch (1977)
    if math.isnan(k):
        return "–"
    for lim, t in ((0.81, "majdnem teljes"), (0.61, "jelentős"), (0.41, "közepes"), (0.21, "mérsékelt")):
        if k >= lim:
            return t
    return "gyenge"


def table_agreement(ratings_csv: Path, results_root: Path, out: Path) -> tuple[dict, list[list[str]]] | None:
    """AI-13: do teachers agree with each other (Krippendorff α), and does the LLM judge agree with them
    (Spearman ρ per criterion, Cohen κ for 'grounded' vs teacher correctness ≥ 4)?"""
    from .analysis import human_analysis
    r = pd.read_csv(ratings_csv)
    qs = load_questions(results_root, r["run_id"].dropna().unique()) if "run_id" in r else pd.DataFrame()
    res = human_analysis(str(ratings_csv), qs, out)
    alphas, rhos = res.get("krippendorff_alpha", {}), res.get("judge_vs_teacher_spearman", {})
    header = ["Szempont", "Tanárok egymás közt (α)", "α értelmezése", "Bíráló–tanár (ρ)", "p", "n kérdés",
              "ρ, κ értelmezése"]
    body = []
    for c in CRITERIA + ["would_use"]:
        a = alphas.get(c, math.nan)
        rr = rhos.get(c, {"rho": math.nan, "p": math.nan, "n": 0})
        body.append([CRIT_HU[c], hu(a), _alpha_hu(a), hu(rr["rho"]), hu(rr["p"], 3), str(rr["n"] or "–"),
                     _rho_hu(rr["rho"])])
    m = rhos.get("mean_of_criteria")
    if m:
        body.append(["A négy szempont átlaga", "–", "", hu(m["rho"]), hu(m["p"], 3), str(m["n"]), _rho_hu(m["rho"])])
    k = res.get("grounded_vs_teacher_correct_kappa", math.nan)
    body.append(["Helyes-e: bíráló „igazolt” vs tanár ≥ 4 (κ)", "–", "", hu(k), "", "", _kappa_hu(k)])
    _draw_table(header, body, out, "tabla3_egyetertes", {len(body) - 1}, left_cols={0},
                title=f"A tanárok és a bíráló egyetértése ({res['n_items']} kérdés, "
                      f"{len(res['raters'])} értékelő)")
    return res, [header] + body


# ---------------------------------------------------------------- text
def write_text(out: Path, ex, summary, metrics, best, sig, steps, has_chunk, pilot: bool,
               best_local=None, rank_rows=None, win=None, extra: dict | None = None) -> None:
    extra = extra or {}
    b = summary.set_index("arm").loc[best]
    runner = summary.iloc[1] if len(summary) > 1 else None
    base = summary.set_index("arm").loc["E0"] if "E0" in set(summary["arm"]) else None
    n_docs = ex["doc_id"].nunique()
    n_seeds = ex["seed"].nunique()
    langs = ", ".join(sorted(ex["language"].dropna().unique())) if "language" in ex else "–"
    metric_list = ", ".join(lab.lower() for _, lab in metrics)
    L = []
    if pilot:
        L += [f"> **PILOT – nem végleges eredmény.** Csak {n_docs} dokumentum; ennyi adatból statisztikailag "
              "szignifikáns különbség nem mutatható ki (páros Wilcoxon-próbához legalább 6 dokumentum kell). "
              "A teljes futás után a `python -m mimir_eval report` ugyanezt a szöveget a végleges számokkal "
              "generálja újra.", ""]
    L += ["## Eredmények", "",
          f"A módszereket {n_docs} dokumentumon ({langs}), dokumentumonként {n_seeds} ismétléssel (seed) "
          f"értékeltük; minden vizsga 10 feleletválasztós kérdésből állt. A minőségi index a következő "
          f"mutatók átlaga: {metric_list}. Mindegyik 0 és 1 közötti, és mindegyiknél a nagyobb érték a jobb. "
          "Az értékeket először dokumentumonként átlagoltuk, majd a dokumentumokra vett bootstrap-mintavétellel "
          "(10 000 minta) 95%-os konfidenciaintervallumot számoltunk. A kérdések helyességét egy független "
          "nyelvi modell (gpt-oss:120b) ítélte meg, amely más modellcsaládba tartozik, mint a kérdéseket író modell.",
          "", "### A legjobb módszer", "",
          f"A legmagasabb minőségi indexet {az(best)} **{best} – {ARM_HU.get(best, (best, ''))[0]}** módszer érte el "
          f"({hu(b['qi'])}" + ("" if math.isnan(b['ci_lo']) else f"; 95% KI: {hu(b['ci_lo'])}–{hu(b['ci_hi'])}")
          + f"), lásd a 2. ábrát. Lényege: {ARM_HU.get(best, ('', ''))[1]}."]
    if base is not None and best != "E0":
        diff = b["qi"] - base["qi"]
        L[-1] += (f" Az alapmódszerhez (E0, {hu(base['qi'])}) képest a különbség {'+' if diff >= 0 else ''}"
                  f"{hu(diff)}.")
    if runner is not None:
        srow = sig.set_index("arm").loc[runner["arm"]] if runner["arm"] in set(sig["arm"]) else None
        p_txt = "" if srow is None or math.isnan(srow["p_holm"]) else \
            f" (páros Wilcoxon-próba, Holm-korrekció: p = {hu(srow['p_holm'], 3)})"
        signif = srow is not None and not math.isnan(srow["p_holm"]) and srow["p_holm"] < 0.05
        L[-1] += (f" A második helyezett {az(runner['arm'])} {runner['arm']} ({hu(runner['qi'])}); a különbség "
                  f"{'statisztikailag szignifikáns' if signif else 'nem szignifikáns'}{p_txt}.")
    L += [""]
    verdict = f"**Győztes: {best} – {ARM_HU.get(best, (best, ''))[0]}** (minőségi index {hu(b['qi'])})."
    if best_local and best_local != best:
        bl = summary.set_index("arm").loc[best_local]
        verdict += (f" Ha az adatok nem hagyhatják el a gépet (csak helyi modell), a legjobb választás "
                    f"{az(best_local)} **{best_local} – {ARM_HU.get(best_local, (best_local, ''))[0]}** "
                    f"({hu(bl['qi'])}).")
    L += [verdict, ""]
    if rank_rows:
        L += ["**1. táblázat – A módszerek összesített rangsora** (`tabla1_osszesito`)", ""] + md_table(rank_rows) + [""]
    if win:
        L += [f"**2. táblázat – A győztes az alapmódszerhez ({win[0]}) képest** (`tabla2_gyoztes_vs_alap`)", ""] \
             + md_table(win[1]) + [""]
    L += ["Mutatónként (3. ábra):", ""]
    for col, lab in metrics:
        L.append(f"- **{lab}:** {best}: {pct(b[col])}" + (f", E0: {pct(base[col])}" if base is not None else ""))
    if "meta_reference_rate" in b and not math.isnan(b["meta_reference_rate"]):
        L.append(f"- **„A szöveg szerint” típusú kérdések aránya:** {best}: {pct(b['meta_reference_rate'])}"
                 + (f", E0: {pct(base['meta_reference_rate'])}" if base is not None else ""))
    L += ["", "### Mit ad hozzá az egyes komponens", ""]
    if steps:
        parts = []
        names = {"E1": "a tervezés", "E2": "az ellenőrzés", "E3": "a fogalomgráf"}
        for a, v, d in steps[1:]:
            parts.append(f"{names[a]} {'+' if d >= 0 else ''}{hu(d)}")
        L.append("Az 5. ábra lépésenként mutatja a minőségi index változását az alapmódszertől a teljes "
                 f"rendszerig: {'; '.join(parts)}.")
    else:
        L.append("(Az E0–E3 lánc hiányos, ezért ez a rész nem készült el.)")
    L += ["", "### Minőség és költség", ""]
    t_best, t_base = b["ido_median_s"], (base["ido_median_s"] if base is not None else math.nan)
    L.append(f"A jobb minőségnek ára van (4. ábra): egy 10 kérdéses vizsga {az(best)} {best} módszerrel medián "
             f"{hu(t_best / 60, 1)} perc" + (f", az alapmódszerrel {hu(t_base / 60, 1)} perc" if base is not None else "")
             + f"; {az(best)} {best} medián {hu(b['llm_hivas_median'], 0)} nyelvimodell-hívást igényel vizsgánként.")
    if has_chunk:
        s = summary.set_index("arm")
        L += ["", "### Darabolás", "",
              "A 6. ábra az alapmódszert hasonlítja össze különböző darabolási változatokkal: "
              + "; ".join(f"{a} ({ARM_HU[a][0].lower()}): {hu(s.loc[a, 'qi'])}"
                          for a in ("E5a", "E0", "E5b", "E5c") if a in s.index) + "."]
    L += _extra_text(extra, summary)
    L += ["", "### Táblázatok és ábrák", "",
          "1. táblázat – A módszerek összesített rangsora (`tabla1_osszesito`).",
          "2. táblázat – A győztes összevetése az alapmódszerrel (`tabla2_gyoztes_vs_alap`).",
          "1. ábra – A vizsgált módszerek felépítése (`abra1_modszerek`).",
          "2. ábra – A módszerek rangsora a minőségi index alapján, 95%-os konfidenciaintervallummal (`abra2_rangsor`).",
          "3. ábra – Az egyes minőségi mutatók módszerenként (`abra3_mutatok`).",
          "4. ábra – Minőség és futási idő (`abra4_minoseg_koltseg`).",
          "5. ábra – Az egyes komponensek hozzájárulása (`abra5_komponensek`)."]
    if has_chunk:
        L.append("6. ábra – A darabolási változatok összehasonlítása (`abra6_darabolas`).")
    if extra.get("agreement"):
        L.append("3. táblázat – A tanárok és a bíráló egyetértése (`tabla3_egyetertes`).")
    if extra.get("sig"):
        L.append("4. táblázat – Páros Wilcoxon-próbák a fő lépésekre (`tabla4_szignifikancia`).")
    if extra.get("lang"):
        L += ["5. táblázat – Magyar és angol dokumentumok (`tabla5_nyelvek`).",
              "7. ábra – Minőségi index nyelvenként (`abra7_nyelvek`)."]
    if extra.get("dataset"):
        L.append("6. táblázat – Az értékelő adatkészlet (`tabla6_adatkeszlet`).")
    if extra.get("n_examples"):
        L.append("Példakérdések a hibaelemzéshez: `peldak.md`.")
    L += ["", f"*Generálva: {date.today().isoformat()}, `python -m mimir_eval report`; adatok: "
          + ", ".join(sorted(ex["run_dir"].unique())) + "*", ""]
    (out / "eredmenyek.md").write_text("\n".join(L), encoding="utf-8")


def _extra_text(extra: dict, summary: pd.DataFrame) -> list[str]:
    L = []
    if extra.get("dataset"):
        info, rows = extra["dataset"]
        langs = ", ".join(f"{n} {LANG_HU.get(lang, lang)}" for lang, n in info["by_lang"].items())
        L += ["", "### Adatkészlet", "",
              f"Az adatkészlet ({info['version']}) {info['n_docs']} dokumentumból áll ({langs}), összesen "
              f"{info['n_gold']} arany (ember által írt) kérdéssel; ebben a jelentésben {info['n_used']} dokumentum "
              "eredménye szerepel (6. táblázat).", "",
              "**6. táblázat – Az értékelő adatkészlet** (`tabla6_adatkeszlet`)", ""] + md_table(rows)
    if extra.get("agreement"):
        res, rows = extra["agreement"]
        k = res.get("grounded_vs_teacher_correct_kappa", math.nan)
        m = (res.get("judge_vs_teacher_spearman") or {}).get("mean_of_criteria") or {"rho": math.nan}
        L += ["", "### A bíráló megbízhatósága", "",
              f"{len(res['raters'])} tanár {res['n_items']} kérdést értékelt vakon, ugyanazzal a skálával, mint a "
              f"bíráló modell. A négy szempont átlagán a bíráló és a tanárok rangkorrelációja ρ = {hu(m['rho'])} "
              f"({_rho_hu(m['rho'])}); a „helyes-e” döntésben Cohen-féle κ = {hu(k)} ({_kappa_hu(k)}). A tanárok "
              "egymás közti egyetértését Krippendorff-féle α méri (3. táblázat).", "",
              "**3. táblázat – A tanárok és a bíráló egyetértése** (`tabla3_egyetertes`)", ""] + md_table(rows)
    else:
        L += ["", "### A bíráló megbízhatósága", "",
              "(A tanári értékelés még nem érkezett be; a `rate-import` után a `report` elkészíti a 3. táblázatot.)"]
    if extra.get("sig"):
        df, rows = extra["sig"]
        n_sig = int((df["p_holm"] < 0.05).sum())
        L += ["", "### Statisztikai próbák", "",
              f"A fő lépéseket páros Wilcoxon-próbával hasonlítottuk össze a dokumentumonkénti minőségi indexen; a "
              f"p-értékeket {az(str(len(df)))} {len(df)} összevetésre Holm-módszerrel korrigáltuk, a hatásméret a rangbiszeriális "
              f"korreláció (r > 0: az új módszer jobb). Szignifikáns (p < 0,05): {n_sig} összevetés.", "",
              "**4. táblázat – Páros Wilcoxon-próbák** (`tabla4_szignifikancia`)", ""] + md_table(rows)
    if extra.get("lang"):
        rows = extra["lang"]
        L += ["", "### Magyar és angol dokumentumok", "",
              "Az 5. táblázat és a 7. ábra nyelvenként mutatja az eredményeket. A két nyelv dokumentumai különbözők "
              "(forrás, téma, hossz), ezért a különbség leíró jellegű, nem ok-okozati.", "",
              "**5. táblázat – Magyar és angol dokumentumok** (`tabla5_nyelvek`)", ""] + md_table(rows)
    if extra.get("n_examples"):
        L += ["", "### Példák", "",
              "Módszerenként egy jó és egy rossz kérdés a bíráló indoklásával a `peldak.md` fájlban található "
              "(a hibaelemzés alapanyaga)."]
    return L


def build_report(results_root: str = "results", name: str | None = None, arms: list[str] | None = None,
                 out_root: str = "report", ratings: str | None = "ratings/ratings.csv") -> Path:
    """ratings: rate-import output; the agreement table (tabla3) is built only when the file exists."""
    root = resolve(results_root)
    ex = load_latest(root, arms)
    metrics = quality_metrics(ex)
    if not metrics:
        raise SystemExit("no quality metrics shared by all arms (were the runs scored with the judge?)")
    ex = add_index(ex, metrics)
    summary = summarize(ex, metrics)
    best = summary.iloc[0]["arm"]
    sig = significance(ex, best, [a for a in summary["arm"] if a != best])
    out = resolve(out_root) / name if name else resolve(out_root)
    out.mkdir(parents=True, exist_ok=True)
    pilot = ex["doc_id"].nunique() < 6
    PILOT["on"] = pilot
    local = summary[summary["helyi"]]
    best_local = local.iloc[0]["arm"] if len(local) else None
    fig_methods(out)
    rank_rows = table_rank(summary, metrics, best, best_local, out)
    win = table_winner(summary, metrics, best, out)
    fig_ranking(summary, best, out)
    fig_metrics(summary, metrics, best, out)
    fig_cost(summary, best, out)
    steps = fig_components(summary, out)
    has_chunk = fig_chunking(summary, out)
    extra = {"agreement": None, "sig": table_significance(ex, out), "lang": table_languages(ex, summary, metrics, out),
             "dataset": table_dataset(ex, root, out)}
    rpath = resolve(ratings) if ratings else None
    if rpath and rpath.exists():
        extra["agreement"] = table_agreement(rpath, root, out)
    extra["n_examples"] = write_examples(load_questions(root, ex["run_dir"].unique()), list(summary["arm"]), out)
    write_text(out, ex, summary, metrics, best, sig, steps, has_chunk, pilot, best_local, rank_rows, win, extra)
    tab = summary.rename(columns={"arm": "modszer", "qi": "minosegi_index"})
    tab.to_csv(out / "eredmenyek_tabla.csv", index=False, encoding="utf-8-sig")
    print(f"[report] best: {best} ({hu(summary.iloc[0]['qi'])}) from {len(summary)} methods, "
          f"{ex['doc_id'].nunique()} documents{' - PILOT' if pilot else ''} -> {out}")
    return out
