"""Az oktatói értékelés számai (5.6. szakasz, H5) -> oktatoi.json és oktatoi.md.

Bemenet: tests/eval/ratings/ratings_v3/ratings.csv (rate-import kimenete) és a hat mintavételezett futás
questions.jsonl-je (a bíró ítéletei). Futtatás a repó gyökeréből: python tdk/elemzes/oktatoi.py
"""
from __future__ import annotations

import json
import math
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "eval"))
from mimir_eval.stats import cohen_kappa, krippendorff_alpha, spearman  # noqa: E402

EVAL = ROOT / "tests" / "eval"
RATINGS = EVAL / "ratings" / "ratings_v3" / "ratings.csv"
RUN_ROOTS = [EVAL / "results_qwen_2026-09", EVAL / "results"]
OUT = Path(__file__).resolve().parent
CRIT = ["correctness", "clarity", "distractor_quality", "bloom_fit"]
GEN = {"qwen2.5": "Qwen", "PULI": "PULI", "gemma3": "Gemma"}
N_BOOT = 2000
rng = np.random.default_rng(7)


def r3(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 3)


def gen_name(g: str) -> str:
    return next(v for k, v in GEN.items() if k in g)


def judge_rows(run_ids) -> pd.DataFrame:
    rows = []
    for rid in run_ids:
        p = next(r / rid / "questions.jsonl" for r in RUN_ROOTS if (r / rid / "questions.jsonl").exists())
        rows += [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    q = pd.DataFrame(rows)
    for c in CRIT:
        q[f"judge_{c}"] = pd.to_numeric(q[f"judge_{c}"], errors="coerce")
    for c in ("grounded", "judge_would_use", "blind_correct"):
        q[c] = q[c].map({"True": True, "False": False, True: True, False: False})
    return q[["uid", "language", *[f"judge_{c}" for c in CRIT], "grounded", "judge_would_use", "blind_correct"]]


def matrix(r: pd.DataFrame, col: str, raters) -> np.ndarray:
    return r.pivot_table(index="rater", columns="item_id", values=col, aggfunc="first").reindex(raters).astype(float).values


def alpha(r, col, raters, level):
    return krippendorff_alpha(matrix(r, col, raters), level)


def alpha_ci(m: np.ndarray, level: str) -> tuple[float, float]:
    """Bootstrap over items (columns)."""
    vals = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, m.shape[1], m.shape[1])
        vals.append(krippendorff_alpha(m[:, idx], level))
    vals = np.array([v for v in vals if not math.isnan(v)])
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def main():
    r = pd.read_csv(RATINGS)
    r["h_would_use"] = r["h_would_use"].map({True: 1.0, False: 0.0, "True": 1.0, "False": 0.0})
    r["generator"] = r["generator"].map(gen_name)
    r["config"] = r["generator"] + " " + r["arm"].str.replace("-gemma3-12b", "", regex=False)
    raters = sorted(r.rater.unique())
    q = judge_rows(r.run_id.unique())
    res: dict = {"raters": raters}

    rated = r.dropna(subset=["h_correctness"])
    res["n_ratings_by_rater"] = rated.groupby("rater").size().to_dict()
    res["n_ratings_by_rater_sheet"] = {f"{a}/{b}": int(n) for (a, b), n in rated.groupby(["rater", "sheet"]).size().items()}

    # ---------------- 1. tanárok egymás közt -------------------------------------------------------
    for name, sub in {"rated60": r[~r.calibration], "all72": r, "calib12": r[r.calibration]}.items():
        a = {}
        for c in CRIT + ["would_use"]:
            lvl = "nominal" if c == "would_use" else "ordinal"
            m = matrix(sub, f"h_{c}", raters)
            a[c] = {"alpha": r3(krippendorff_alpha(m, lvl))}
            if name == "rated60":
                lo, hi = alpha_ci(m, lvl)
                a[c]["ci"] = [r3(lo), r3(hi)]
        res[f"alpha_teachers_{name}"] = a
    main_set = r[~r.calibration].copy()
    # páronkénti α és leave-one-out a 60 kérdésen
    pair = {}
    for c in CRIT + ["would_use"]:
        lvl = "nominal" if c == "would_use" else "ordinal"
        pair[c] = {f"{x}-{y}": r3(alpha(main_set, f"h_{c}", [x, y], lvl)) for x, y in combinations(raters, 2)}
    res["alpha_pairwise"] = pair
    res["alpha_leave_one_out"] = {
        out: {c: r3(alpha(main_set, f"h_{c}", [x for x in raters if x != out], "nominal" if c == "would_use" else "ordinal"))
              for c in CRIT + ["would_use"]} for out in raters}
    # értékelőnkénti átlagok (szigor)
    res["rater_means"] = {
        rt: {**{c: r3(g[f"h_{c}"].mean()) for c in CRIT}, "would_use": r3(g["h_would_use"].mean()), "n": int(g.h_correctness.notna().sum())}
        for rt, g in main_set.groupby("rater")}

    # ---------------- 2. bíró és tanárok -------------------------------------------------------------
    item = main_set.groupby(["item_id", "uid", "config", "generator", "arm"]).agg(
        **{f"h_{c}": (f"h_{c}", "mean") for c in CRIT},
        **{f"hmed_{c}": (f"h_{c}", "median") for c in CRIT},
        h_would_use=("h_would_use", "mean"), n_raters=("h_correctness", "count")).reset_index()
    item = item.merge(q, on="uid", how="left")
    item["h_mean"] = item[[f"h_{c}" for c in CRIT]].mean(axis=1)
    item["judge_mean"] = item[[f"judge_{c}" for c in CRIT]].mean(axis=1)
    res["n_items_with_judge"] = int(item.judge_correctness.notna().sum())
    jt = {}
    for c in CRIT + ["mean"]:
        h, j = (item["h_mean"], item["judge_mean"]) if c == "mean" else (item[f"h_{c}"], item[f"judge_{c}"])
        s = spearman(j, h)
        jt[c] = {"rho": r3(s["rho"]), "p": r3(s["p"]), "n": s["n"],
                 "judge_mean": r3(j.mean()), "teacher_mean": r3(h.mean())}
    # α a bíró és a tanárok mediánja között (felfelé kerekítve a .5-öt) és a bíró mint hatodik értékelő
    for c in CRIT:
        med = np.floor(item[f"hmed_{c}"] + 0.5)
        jm = np.vstack([item[f"judge_{c}"].values, med.values])
        jt[c]["alpha_judge_vs_median"] = r3(krippendorff_alpha(jm, "ordinal"))
        jt[c]["alpha_judge_vs_median_ci"] = [r3(x) for x in alpha_ci(jm, "ordinal")]
        m = matrix(main_set, f"h_{c}", raters)
        jrow = item.set_index("item_id").reindex(sorted(main_set.item_id.unique()))[f"judge_{c}"].values
        jt[c]["alpha_with_judge"] = r3(krippendorff_alpha(np.vstack([m, jrow]), "ordinal"))
        # páronként: bíró–tanár átlag vs tanár–tanár átlag
        jp = [krippendorff_alpha(np.vstack([m[i], jrow]), "ordinal") for i in range(len(raters))]
        tp = [krippendorff_alpha(np.vstack([m[i], m[k]]), "ordinal") for i, k in combinations(range(len(raters)), 2)]
        jt[c]["alpha_judge_teacher_pairs_mean"] = r3(np.nanmean(jp))
        jt[c]["alpha_judge_teacher_pairs"] = dict(zip(raters, [r3(x) for x in jp]))
        jt[c]["alpha_teacher_pairs_mean"] = r3(np.nanmean(tp))
    res["judge_vs_teachers"] = jt
    # bináris: bíró „alátámasztott” vs tanári többség helyesség >= 4; felhasználnám vs többség
    maj_ok = main_set.assign(ok=main_set.h_correctness >= 4).dropna(subset=["h_correctness"]).groupby("item_id").ok.mean()
    maj_use = main_set.dropna(subset=["h_would_use"]).groupby("item_id").h_would_use.mean()
    it = item.set_index("item_id")
    t_ok = [None if pd.isna(v) else bool(v > 0.5) for v in maj_ok.reindex(it.index)]
    t_use = [None if pd.isna(v) else bool(v > 0.5) for v in maj_use.reindex(it.index)]
    j_ok = [None if pd.isna(v) else bool(v) for v in it.grounded]
    j_use = [None if pd.isna(v) else bool(v) for v in it.judge_would_use]
    res["kappa"] = {
        "grounded_vs_teacher_correct": r3(cohen_kappa(j_ok, t_ok)),
        "would_use_judge_vs_teachers": r3(cohen_kappa(j_use, t_use)),
        "judge_would_use_rate": r3(np.mean([x for x in j_use if x is not None])),
        "teacher_majority_would_use_rate": r3(np.mean([x for x in t_use if x is not None])),
        "judge_grounded_rate": r3(np.mean([x for x in j_ok if x is not None])),
        "teacher_majority_correct_rate": r3(np.mean([x for x in t_ok if x is not None])),
        "confusion_would_use": {f"judge_{a}_teacher_{b}": int(sum(1 for x, y in zip(j_use, t_use) if x is a and y is b))
                                for a in (True, False) for b in (True, False)},
        "confusion_correct": {f"judge_{a}_teacher_{b}": int(sum(1 for x, y in zip(j_ok, t_ok) if x is a and y is b))
                              for a in (True, False) for b in (True, False)},
    }
    # teacher-vs-teacher kappa on would_use for reference (mean over pairs)
    wu = main_set.pivot_table(index="item_id", columns="rater", values="h_would_use", aggfunc="first")
    kp = []
    for x, y in combinations(raters, 2):
        a = [None if pd.isna(v) else bool(v) for v in wu[x]]
        b = [None if pd.isna(v) else bool(v) for v in wu[y]]
        kp.append(cohen_kappa(a, b))
    res["kappa"]["would_use_teacher_pairs_mean"] = r3(np.nanmean(kp))

    # ---------------- 3. minőség konfigurációnként a tanárok szerint --------------------------------
    def boot_mean(v):
        v = np.asarray(v, float)
        v = v[~np.isnan(v)]
        bs = [rng.choice(v, len(v)).mean() for _ in range(N_BOOT)]
        return [r3(v.mean()), r3(np.percentile(bs, 2.5)), r3(np.percentile(bs, 97.5))]

    by = {}
    for cfg, g in item.groupby("config"):
        by[cfg] = {"n": int(len(g)), "teacher_mean": boot_mean(g.h_mean), "teacher_would_use": r3(g.h_would_use.mean()),
                   **{f"t_{c}": r3(g[f"h_{c}"].mean()) for c in CRIT},
                   "judge_mean": r3(g.judge_mean.mean()), "judge_would_use": r3(g.judge_would_use.astype(float).mean()),
                   "judge_grounded": r3(g.grounded.astype(float).mean())}
    res["by_config"] = by
    res["by_arm"] = {a: {"n": int(len(g)), "teacher_mean": boot_mean(g.h_mean), "teacher_would_use": r3(g.h_would_use.mean()),
                         "judge_mean": r3(g.judge_mean.mean())}
                     for a, g in item.assign(arm2=item.arm.str.replace("-gemma3-12b", "", regex=False)).groupby("arm2")}
    res["by_generator"] = {a: {"n": int(len(g)), "teacher_mean": boot_mean(g.h_mean), "teacher_would_use": r3(g.h_would_use.mean()),
                               "judge_mean": r3(g.judge_mean.mean())} for a, g in item.groupby("generator")}
    res["by_language"] = {a: {"n": int(len(g)), "teacher_mean": r3(g.h_mean.mean()), "teacher_would_use": r3(g.h_would_use.mean()),
                              "judge_mean": r3(g.judge_mean.mean()),
                              "rho_mean": r3(spearman(g.judge_mean, g.h_mean)["rho"])} for a, g in item.groupby("language")}
    # Mann–Whitney: E2 vs B-doc-L on the teacher item means (pooled over generators and per generator)
    from scipy.stats import mannwhitneyu
    item["arm2"] = item.arm.str.replace("-gemma3-12b", "", regex=False)
    mw = {}
    for gname, g in [("all", item), *item.groupby("generator")]:
        a, b = g[g.arm2 == "E2"].h_mean.dropna(), g[g.arm2 == "B-doc-L"].h_mean.dropna()
        t = mannwhitneyu(a, b, alternative="two-sided")
        mw[gname] = {"E2": r3(a.mean()), "B-doc-L": r3(b.mean()), "n": [len(a), len(b)], "p": r3(t.pvalue)}
    res["E2_vs_Bdoc"] = mw
    # rangsor-egyezés a hat konfiguráción (bíró vs tanár átlag)
    cfg = pd.DataFrame(by).T
    res["config_rank_rho"] = r3(spearman(cfg.judge_mean.astype(float), cfg.teacher_mean.map(lambda v: v[0]).astype(float))["rho"])
    # hibás tételek: legalább egy tanár helyesség 1 vagy 2
    item["bad"] = main_set.groupby("item_id").h_correctness.min().reindex(item.item_id).values <= 2
    res["items_low_correctness_any"] = int(item.bad.sum())
    res["items_low_correctness_majority"] = int((maj_ok.reindex(item.item_id).values <= 0.5).sum())
    res["judge_on_teacher_wrong"] = {
        "n": int((~np.array([x if x is not None else True for x in t_ok])).sum()),
        "judge_grounded": int(sum(1 for x, y in zip(j_ok, t_ok) if y is False and x is True)),
        "judge_would_use": int(sum(1 for x, y in zip(j_use, t_ok) if y is False and x is True))}
    item.to_csv(OUT / "oktatoi_kerdesek.csv", index=False)
    (OUT / "oktatoi.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    write_md(res)
    print("wrote", OUT / "oktatoi.json", "and oktatoi.md")


def write_md(res):
    L = ["# Oktatói értékelés (generálva: tdk/elemzes/oktatoi.py)", "",
         f"Értékelők: {res['raters']}; értékelések (kitöltött): {res['n_ratings_by_rater']}", "",
         "## Tanárok egymás közt (Krippendorff-α; ordinális, a felhasználnám nominális)", "",
         "| szempont | 60 kérdés | 95% CI | 72 (kalibrációval) | 12 kalibrációs |", "|---|---|---|---|---|"]
    for c in CRIT + ["would_use"]:
        a = res["alpha_teachers_rated60"][c]
        L.append(f"| {c} | {a['alpha']} | {a['ci']} | {res['alpha_teachers_all72'][c]['alpha']} | "
                 f"{res['alpha_teachers_calib12'][c]['alpha']} |")
    L += ["", "Leave-one-out α: " + json.dumps(res["alpha_leave_one_out"], ensure_ascii=False), "",
          "Páronkénti α: " + json.dumps(res["alpha_pairwise"], ensure_ascii=False), "",
          "Értékelőnkénti átlagok: " + json.dumps(res["rater_means"], ensure_ascii=False), "",
          "## Bíró és tanárok", "",
          "| szempont | ρ | p | n | bíró átlag | tanár átlag | α bíró–medián | α tanárok+bíró | α bíró–tanár pár (átl.) | α tanár–tanár pár (átl.) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for c, v in res["judge_vs_teachers"].items():
        L.append(f"| {c} | {v['rho']} | {v['p']} | {v['n']} | {v['judge_mean']} | {v['teacher_mean']} | "
                 f"{v.get('alpha_judge_vs_median', '')} {v.get('alpha_judge_vs_median_ci', '')} | {v.get('alpha_with_judge', '')} | "
                 f"{v.get('alpha_judge_teacher_pairs_mean', '')} | {v.get('alpha_teacher_pairs_mean', '')} |")
    L += ["", "κ: " + json.dumps(res["kappa"], ensure_ascii=False), "",
          "## Konfigurációnként (tanári átlag [átlag, CI], felhasználnám-arány; bíró)", ""]
    for k, v in res["by_config"].items():
        L.append(f"- {k}: {json.dumps(v, ensure_ascii=False)}")
    L += ["", "Karonként: " + json.dumps(res["by_arm"], ensure_ascii=False),
          "", "Generátoronként: " + json.dumps(res["by_generator"], ensure_ascii=False),
          "", "Nyelvenként: " + json.dumps(res["by_language"], ensure_ascii=False),
          "", "E2 vs B-doc-L (Mann–Whitney): " + json.dumps(res["E2_vs_Bdoc"], ensure_ascii=False),
          "", f"Konfiguráció-rangsor ρ (bíró vs tanár, 6 konf.): {res['config_rank_rho']}",
          "", f"Legalább egy tanár szerint hibás (helyesség ≤ 2): {res['items_low_correctness_any']}; "
              f"többség szerint nem helyes (< 4): {res['items_low_correctness_majority']}; "
              f"ebből a bíró alátámasztottnak tartja / felhasználná: {res['judge_on_teacher_wrong']}"]
    (OUT / "oktatoi.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
