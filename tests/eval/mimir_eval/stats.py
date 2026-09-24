"""Statistics used in the paper: bootstrap CIs, paired Wilcoxon + Holm, agreement measures."""
from __future__ import annotations

import math

import numpy as np
from scipy import stats as sps


def bootstrap_ci(values, n_boot: int = 10_000, alpha: float = 0.05, seed: int = 0) -> tuple[float, float, float]:
    """Mean and percentile CI. Pass one value per document so documents are the resampling unit."""
    v = np.asarray([x for x in values if x is not None and not (isinstance(x, float) and math.isnan(x))], float)
    if len(v) == 0:
        return (math.nan, math.nan, math.nan)
    if len(v) == 1:
        return (float(v[0]), math.nan, math.nan)
    rng = np.random.default_rng(seed)
    boots = v[rng.integers(0, len(v), size=(n_boot, len(v)))].mean(axis=1)
    return float(v.mean()), float(np.quantile(boots, alpha / 2)), float(np.quantile(boots, 1 - alpha / 2))


def paired_wilcoxon(a, b) -> dict:
    """a, b: paired per-document values. Effect size = matched-pairs rank-biserial r (-1..1, >0 means b > a)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    mask = ~(np.isnan(a) | np.isnan(b))
    a, b = a[mask], b[mask]
    d = b - a
    nz = d[d != 0]
    out = {"n_pairs": int(len(d)), "mean_a": float(a.mean()) if len(a) else math.nan,
           "mean_b": float(b.mean()) if len(b) else math.nan,
           "mean_diff": float(d.mean()) if len(d) else math.nan}
    if len(nz) == 0:
        return {**out, "W": math.nan, "p": 1.0 if len(d) else math.nan, "r_rb": 0.0 if len(d) else math.nan}
    ranks = sps.rankdata(np.abs(nz))
    t_plus, t_minus = ranks[nz > 0].sum(), ranks[nz < 0].sum()
    res = sps.wilcoxon(a, b, zero_method="wilcox", alternative="two-sided")
    return {**out, "W": float(res.statistic), "p": float(res.pvalue),
            "r_rb": float((t_plus - t_minus) / (t_plus + t_minus))}


def holm(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values (NaN kept as NaN)."""
    idx = [i for i, p in enumerate(pvals) if p is not None and not math.isnan(p)]
    order = sorted(idx, key=lambda i: pvals[i])
    m = len(order)
    adj = [math.nan] * len(pvals)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


def krippendorff_alpha(data, level: str = "ordinal") -> float:
    """data: raters x units matrix, NaN = missing. level: nominal | ordinal | interval."""
    x = np.asarray(data, float)
    values = np.unique(x[~np.isnan(x)])
    if len(values) < 2:
        return math.nan
    vidx = {v: i for i, v in enumerate(values)}
    k = len(values)
    o = np.zeros((k, k))
    for u in range(x.shape[1]):
        col = x[:, u][~np.isnan(x[:, u])]
        m = len(col)
        if m < 2:
            continue
        for i in range(m):
            for j in range(m):
                if i != j:
                    o[vidx[col[i]], vidx[col[j]]] += 1.0 / (m - 1)
    n_c = o.sum(axis=1)
    n = n_c.sum()
    if n <= 1:
        return math.nan
    delta = np.zeros((k, k))
    for c in range(k):
        for d in range(k):
            if level == "nominal":
                delta[c, d] = 0.0 if c == d else 1.0
            elif level == "interval":
                delta[c, d] = (values[c] - values[d]) ** 2
            else:  # ordinal
                lo, hi = min(c, d), max(c, d)
                delta[c, d] = (n_c[lo:hi + 1].sum() - (n_c[c] + n_c[d]) / 2.0) ** 2
    d_o = (o * delta).sum()
    d_e = (np.outer(n_c, n_c) * delta).sum() / (n - 1)
    return float(1.0 - d_o / d_e) if d_e > 0 else math.nan


def spearman(a, b) -> dict:
    a, b = np.asarray(a, float), np.asarray(b, float)
    mask = ~(np.isnan(a) | np.isnan(b))
    if mask.sum() < 3:
        return {"rho": math.nan, "p": math.nan, "n": int(mask.sum())}
    res = sps.spearmanr(a[mask], b[mask])
    return {"rho": float(res.statistic), "p": float(res.pvalue), "n": int(mask.sum())}


def cohen_kappa(a, b) -> float:
    a, b = list(a), list(b)
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if not pairs:
        return math.nan
    cats = sorted({p for pr in pairs for p in pr}, key=str)
    n = len(pairs)
    po = sum(1 for x, y in pairs if x == y) / n
    pe = sum((sum(1 for x, _ in pairs if x == c) / n) * (sum(1 for _, y in pairs if y == c) / n) for c in cats)
    return float((po - pe) / (1 - pe)) if pe < 1 else math.nan
