"""A dolgozat adatábrái a szamok.json-ból (futtatás előtte: elemzes.py).

    python tdk/elemzes/abrak.py      ->  tdk/figures/f1_rangsor.pdf … f5_forrasok.pdf
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

HERE = Path(__file__).resolve().parent
FIG = HERE.parent / "figures"
D = json.loads((HERE / "szamok.json").read_text(encoding="utf-8"))
S = D["sets"]

# első három kategoriális slot (minden páron validált), plusz eltérő jelölőforma
MODELS = [("qwen", "Qwen2.5-7B (6 dok.)", "#2a78d6", "s"),
          ("puli", "PULI-LlumiX 8B (30 dok.)", "#eb6834", "o"),
          ("gemma", "Gemma 3 12B (30 dok.)", "#1baf7a", "D")]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
                     "pdf.fonttype": 42})
COMMA = FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ","))
COMMA2 = FuncFormatter(lambda v, _: f"{v:.2f}".replace(".", ","))
NAME = {"B-doc-L": "B-doc-L – teljes dok., helyi", "B-doc-S": "B-doc-S – teljes dok., szerver",
        "E0": "E0 – naiv RAG", "E1": "E1 – tervezés", "E2": "E2 – tervezés + ellenőrzés",
        "E3": "E3 – + fogalomgráf", "E2f": "E2f – vak próba nélkül", "E2h": "E2h – hibrid keresés",
        "E2x": "E2x – csak szabályok*", "E4": "E4 – naiv RAG, szerver", "E4b": "E4b – E2, szerver",
        "E5a": "E5a – régi kódoló", "E5b": "E5b – szórásalapú küszöb", "E5c": "E5c – rögzített darabok"}


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(HERE / f"{name}.png", dpi=110, bbox_inches="tight")   # előnézet
    plt.close(fig)


def q(key, arm):
    a = S[key]["arms"].get(arm)
    return (a["Q"], a["ci"]) if a else (None, None)


def f1_rangsor():
    order = ["E2", "E2f", "E2h", "E2x", "E3", "E1", "B-doc-L", "E5a", "E5c", "E5b", "E0",
             "B-doc-S", "E4b", "E4"]
    fig, ax = plt.subplots(figsize=(6.3, 5.0))
    offs = {"qwen": -0.24, "puli": 0.0, "gemma": 0.24}
    for i, arm in enumerate(order):
        for key, lab, col, mk in MODELS:
            m, ci = q(key, arm)
            if m is None:
                continue
            y = i + offs[key]
            if ci and ci[0] is not None:
                ax.plot(ci, [y, y], color=col, lw=2, solid_capstyle="round", alpha=.55)
            ax.plot(m, y, mk, color=col, ms=6, mec="white", mew=1.0,
                    label=lab if i == 0 or (arm == "B-doc-S" and key == "qwen") else None)
    ax.axhline(10.5, color=GRID, lw=1)
    ax.text(0.005, 11.0, "csak az előzetes vizsgálatban (szervermodell)", color=INK2, fontsize=7.5,
            transform=ax.get_yaxis_transform())
    ax.set_yticks(range(len(order)), [NAME[a] for a in order])
    ax.invert_yaxis()
    ax.set_xlim(0, 1.02)
    ax.xaxis.set_major_formatter(COMMA)
    ax.set_xlabel("Minőségi index (Q), dokumentumonkénti átlag, 95 %-os bootstrap-intervallum")
    ax.grid(axis="x", color=GRID, lw=.6)
    h, lab = ax.get_legend_handles_labels()
    seen = dict(zip(lab, h))
    ax.legend(seen.values(), seen.keys(), loc="lower left", fontsize=8, bbox_to_anchor=(0, 1.0), ncol=3,
              handletextpad=.3, columnspacing=1.0)
    save(fig, "f1_rangsor")


def f2_lepesek():
    steps = ["E0", "E1", "E2"]
    fig, ax = plt.subplots(figsize=(6.3, 3.3))
    dy = {"qwen": 0.035, "puli": 0.0, "gemma": -0.035}   # a közeli címkék szétválasztása
    for key, lab, col, mk in MODELS:
        ys = [q(key, a)[0] for a in steps]
        ax.plot(range(3), ys, "-", color=col, lw=2)
        ax.plot(range(3), ys, mk, color=col, ms=7, mec="white", mew=1.0, label=lab)
        b = q(key, "B-doc-L")[0]
        ax.plot([2.85, 3.35], [b, b], "--", color=col, lw=2)
        ax.text(3.42, b + (dy[key] if key != "puli" else 0), f"{b:.2f}".replace(".", ","), va="center",
                fontsize=8, color=INK2)
        ax.text(-0.08, ys[0], f"{ys[0]:.2f}".replace(".", ","), ha="right", va="center", fontsize=8, color=INK2)
        ax.text(2.1, ys[2] + dy[key], f"{ys[2]:.2f}".replace(".", ","), ha="left", va="center", fontsize=8,
                color=INK2)
    ax.axvline(2.55, color=GRID, lw=1)
    ax.set_xticks([0, 1, 2, 3.1], ["E0\nnaiv RAG", "E1\n+ vizsgaterv", "E2\n+ ellenőrző lánc",
                                   "B-doc-L\nteljes dokumentum"])
    ax.set_xlim(-0.45, 3.75)
    ax.set_ylim(0, 1.02)
    ax.yaxis.set_major_formatter(COMMA)
    ax.set_ylabel("Minőségi index (Q)")
    ax.grid(axis="y", color=GRID, lw=.6)
    ax.legend(loc="lower right", fontsize=8)
    save(fig, "f2_lepesek")


def f3_dokumentumok():
    arms = ["E0", "B-doc-L", "E1", "E2"]
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 3.0), sharey=True)
    for ax, (key, lab, col, mk) in zip(axes, MODELS[1:]):
        data = [list(S[key]["per_doc_Q"][a].values()) for a in arms]
        bp = ax.boxplot(data, widths=.5, patch_artist=True, showfliers=False,
                        medianprops={"color": INK, "lw": 1.5}, whiskerprops={"color": INK2},
                        capprops={"color": INK2}, boxprops={"facecolor": col + "33", "edgecolor": INK2})
        for i, d in enumerate(data):
            xs = [i + 1 + (j % 7 - 3) * 0.035 for j in range(len(d))]
            ax.plot(xs, d, mk, color=col, ms=3.5, alpha=.85, mec="none")
        ax.set_xticks(range(1, 5), arms)
        ax.set_title(lab, fontsize=9, color=INK)
        ax.grid(axis="y", color=GRID, lw=.6)
        ax.axhline(0.7, color=INK2, lw=.8, ls=":")
    axes[0].set_ylabel("Q dokumentumonként")
    axes[0].yaxis.set_major_formatter(COMMA)
    axes[0].set_ylim(-0.02, 1.03)
    axes[0].text(4.45, 0.71, "0,7", fontsize=7, color=INK2)
    save(fig, "f3_dokumentumok")


def f4_minoseg_ido():
    fig, ax = plt.subplots(figsize=(6.3, 3.4))
    # csak a kulcskonfigurációk kapnak címkét, modellenként eltolva, hogy ne fedjék egymást
    show = {"qwen": {"E0": (4, -9), "E2": (-6, 6), "B-doc-L": (5, -2), "B-doc-S": (5, -9), "E4b": (-24, -11)},
            "puli": {"E0": (4, 3), "E2": (-4, 6), "B-doc-L": (5, 0), "E1": (-6, 6)},
            "gemma": {"E0": (5, -2), "E2": (4, 5), "B-doc-L": (5, 3)}}
    for key, lab, col, mk in MODELS:
        for arm, a in S[key]["arms"].items():
            t = a["time_median_min"]
            if not t or arm == "E4":
                continue
            ax.plot(t, a["Q"], mk, color=col, ms=6, mec="white", mew=.8)
            if arm in show[key]:
                ax.annotate(arm, (t, a["Q"]), xytext=show[key][arm], textcoords="offset points", fontsize=7,
                            color=INK2)
    for key, lab, col, mk in MODELS:
        ax.plot([], [], mk, color=col, ms=6, label=lab)
    ax.set_xscale("log")
    ax.set_xticks([0.25, 0.5, 1, 2, 5, 10, 20, 50, 100], ["0,25", "0,5", "1", "2", "5", "10", "20", "50", "100"])
    ax.set_xlabel("Medián futási idő vizsgánként (perc, logaritmikus skála)")
    ax.set_ylabel("Minőségi index (Q)")
    ax.yaxis.set_major_formatter(COMMA)
    ax.set_ylim(0.2, 1.02)
    ax.grid(color=GRID, lw=.6)
    ax.legend(loc="lower right", fontsize=8)
    save(fig, "f4_minoseg_ido")


def f5_forrasok():
    arms = ["E0", "B-doc-L", "E1", "E2"]
    srcs = [("hu-sajat", "saját magyar (3)"), ("hu-wiki", "magyar Wikipédia (24)"), ("en-openstax", "angol OpenStax (3)")]
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.8), sharey=True)
    hatch = ["", "///", ".."]
    for ax, (key, lab, col, mk) in zip(axes, MODELS[1:]):
        w = .26
        for j, (s, slab) in enumerate(srcs):
            ys = [S[key]["subsets"][a].get(s, [None])[0] for a in arms]
            ax.bar([i + (j - 1) * (w + .02) for i in range(4)], ys, w, color=col, alpha=[1, .6, .3][j],
                   hatch=hatch[j], edgecolor="white", lw=.5, label=slab)
        ax.set_xticks(range(4), arms)
        ax.set_title(lab, fontsize=9, color=INK)
        ax.grid(axis="y", color=GRID, lw=.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Q (dokumentumonkénti átlag)")
    axes[0].yaxis.set_major_formatter(COMMA)
    axes[0].set_ylim(0, 1.05)
    axes[1].legend(loc="upper left", fontsize=7, bbox_to_anchor=(-0.9, 1.32), ncol=3)
    save(fig, "f5_forrasok")


if __name__ == "__main__":
    for f in (f1_rangsor, f2_lepesek, f3_dokumentumok, f4_minoseg_ido, f5_forrasok):
        f()
    print("ábrák kész:", FIG)
