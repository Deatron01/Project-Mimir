"""A TDK dolgozat összes számának egyetlen forrása.

Beolvassa a három futáskészletet, és a `szamok.md` (olvasható) és `szamok.json` (gépi) fájlba írja
a dolgozatban közölt értékeket. Futtatás a repó gyökeréből:

    python tdk/elemzes/elemzes.py

Futáskészletek
  qwen   tests/eval/results_qwen_2026-09   Qwen2.5-7B, 6 dokumentum, a szerverkarokkal (szept. 27-28.)
  puli   tests/eval/results                PULI-LlumiX-Llama-3.1 8B, 30 dokumentum (okt.)
  gemma  tests/eval/results                Gemma 3 12B, 30 dokumentum (okt. vége)

A minőségi index és a statisztika a kiértékelő keretrendszer (tests/eval/mimir_eval) definícióit
követi: Q = (F + G + A + V) / 4 vizsgánként, a sikertelen vizsga Q-ja 0, a 'error' státuszú
(infrastruktúra-) hibák kimaradnak; az elemzés egysége a dokumentum.
"""
from __future__ import annotations

import ast
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "eval"))
from mimir_eval.stats import bootstrap_ci, cohen_kappa, holm, paired_wilcoxon  # noqa: E402

OUT = Path(__file__).resolve().parent
SETS = {
    "qwen": (ROOT / "tests/eval/results_qwen_2026-09", lambda n: True, ""),
    "puli": (ROOT / "tests/eval/results", lambda n: "gemma" not in n, ""),
    "gemma": (ROOT / "tests/eval/results", lambda n: "gemma3-12b" in n, "-gemma3-12b"),
}
MODEL_HU = {"qwen": "Qwen2.5-7B", "puli": "PULI-LlumiX 8B", "gemma": "Gemma 3 12B"}
QCOLS = ["format_compliant", "grounding_rate", "blind_answerability", "distractor_validity"]
PROBLEM_KEYS = [
    ("A válaszok száma vagy formája", "forma"),
    ("A kérdés a szövegre/dokumentumra", "meta"),
    ("A kérdés szövege elárulja", "szivargas"),
    ("A kérdés ne a forrás egy kijelentő", "nem_kerdes"),
    ("Adj meg a 'citations'", "hivatkozas"),
    ("A megjelölt helyes választ", "kulcs_nem_igazolt"),
    ("Legalább egy disztraktor", "diszt_igaz"),
    ("A kérdés kétértelmű", "ketertelmu"),
    ("Egy független megoldó", "vak_elteres"),
    ("Túl hasonló", "duplikatum"),
]
HIGHER = {"apply", "analyze", "evaluate", "create"}


def tf(v) -> float:
    if isinstance(v, str):
        v = {"True": True, "False": False, "true": True, "false": False}.get(v, v)
    if isinstance(v, (bool, np.bool_)):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return math.nan


def latest_runs(root: Path, keep, suffix: str) -> dict[str, Path]:
    latest: dict[str, Path] = {}
    for rd in sorted(p for p in root.iterdir() if (p / "exam_metrics.csv").exists() and keep(p.name)):
        name = json.loads((rd / "run.json").read_text(encoding="utf-8"))["config"]["name"]
        arm = name[: -len(suffix)] if suffix and name.endswith(suffix) else name
        latest[arm] = rd
    return latest


def doc_meta(doc_id: str) -> tuple[str, str]:
    if doc_id.startswith("hu-wiki"):
        src = "hu-wiki"
    elif doc_id.startswith("hu-"):
        src = "hu-sajat"
    else:
        src = "en-openstax"
    length = "short"
    for L in ("short", "medium", "long"):
        if f"-{L}-" in doc_id:
            length = L
    return src, length


def load_set(key: str):
    root, keep, suffix = SETS[key]
    runs = latest_runs(root, keep, suffix)
    ex_frames, q_frames, exams = [], [], []
    for arm, rd in runs.items():
        df = pd.read_csv(rd / "exam_metrics.csv")
        df["arm"], df["run_dir"] = arm, rd.name
        ex_frames.append(df)
        qp = rd / "questions.jsonl"
        if qp.exists():
            qs = pd.read_json(qp, lines=True, dtype=False)
            qs["arm"] = arm
            q_frames.append(qs)
        for line in (rd / "exams.jsonl").open(encoding="utf-8"):
            x = json.loads(line)
            x.pop("doc_text", None), x.pop("chunks", None), x.pop("context_text", None), x.pop("raw_text", None)
            x["arm"] = arm
            exams.append(x)
    ex = pd.concat(ex_frames, ignore_index=True)
    n_infra = int((ex["status"] == "error").sum())
    ex = ex[ex["status"] != "error"].copy()
    for c in QCOLS + ["valid_json", "count_ok"]:
        if c in ex:
            ex[c] = ex[c].map(tf)
    vals = ex[QCOLS].apply(pd.to_numeric, errors="coerce")
    ex["Q"] = vals.mean(axis=1, skipna=True)
    ex[["source", "length"]] = ex["doc_id"].apply(lambda d: pd.Series(doc_meta(d)))
    qs = pd.concat(q_frames, ignore_index=True) if q_frames else pd.DataFrame()
    return runs, ex, qs, exams, n_infra


def per_doc(ex, arm, col="Q", sub=None):
    s = ex[ex.arm == arm] if sub is None else ex[(ex.arm == arm) & sub]
    return s.groupby("doc_id")[col].apply(lambda v: pd.to_numeric(v, errors="coerce").mean()).dropna()


def r3(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 3)


def summarize(key, ex, qs, exams):
    rows = {}
    ex_by_arm = defaultdict(list)
    for x in exams:
        ex_by_arm[x["arm"]].append(x)
    for arm in sorted(ex["arm"].unique()):
        d = per_doc(ex, arm)
        m, lo, hi = bootstrap_ci(d.values)
        sub = ex[ex.arm == arm]
        row = {"Q": r3(m), "ci": [r3(lo), r3(hi)], "n_docs": len(d), "n_exams": len(sub),
               "Q_min_doc": r3(d.min()), "docs_below_0.7": int((d < 0.7).sum()),
               "failed_exams": int((sub["status"] != "ok").sum())}
        for c in QCOLS + ["coverage", "leakage_rate", "non_question_rate", "duplicate_rate",
                          "meta_reference_rate", "recall@3"]:
            if c in sub:
                row[c] = r3(per_doc(ex, arm, c).mean())
        ok = sub[sub["status"] == "ok"]
        row["questions_per_exam"] = r3(pd.to_numeric(sub["n_generated"], errors="coerce").fillna(0).mean())
        row["time_median_min"] = r3(pd.to_numeric(sub["total_s"], errors="coerce").median() / 60)
        row["calls_median"] = r3(pd.to_numeric(sub["llm_calls"], errors="coerce").median())
        row["unverified_mean"] = r3(pd.to_numeric(sub.get("unverified"), errors="coerce").mean())
        # VRAM: model + runtime = peak - baseline (per exam), and the peak itself
        peak, model_mib, ps = [], [], []
        llm_err, skipped, parse_fail = 0, 0, 0
        for x in ex_by_arm[arm]:
            if x.get("vram_peak_mib") and x.get("vram_baseline_mib") is not None:
                peak.append(x["vram_peak_mib"])
                model_mib.append(x["vram_peak_mib"] - x["vram_baseline_mib"])
            for p in x.get("ollama_ps") or []:      # the model's own footprint as Ollama reports it
                ps.append(p.get("size_mib"))
            llm = x.get("llm") or {}
            llm_err += llm.get("errors", 0) or 0
            parse_fail += llm.get("parse_failures", 0) or 0
            skipped += (x.get("blueprint") or {}).get("verifier_skipped", 0) or 0
        # judge coverage and a robustness check of Q: when every judge call of an exam failed, the
        # per-exam Q falls back to format (+ blind) only; Q_pooled pools G/A/V per document over all
        # successfully judged questions instead, so a failed judge call can only cost precision
        q_all = qs[qs.arm == arm] if len(qs) else pd.DataFrame()
        if len(q_all):
            row["judge_review_coverage"] = r3(q_all["judge_correctness"].notna().mean())
            row["judge_blind_coverage"] = r3(q_all["blind_correct"].notna().mean())
            g = q_all.assign(G=q_all["grounded"].map(tf), A=q_all["blind_correct"].map(tf),
                             V=pd.to_numeric(q_all["distractor_valid_rate"], errors="coerce"))
            pooled = g.groupby("doc_id")[["G", "A", "V"]].mean()
            fdoc = per_doc(ex, arm, "format_compliant")
            pooled = pooled.join(fdoc.rename("F"), how="right")
            qp = pooled[["F", "G", "A", "V"]].mean(axis=1, skipna=True)
            m2, lo2, hi2 = bootstrap_ci(qp.dropna().values)
            row["Q_pooled"], row["Q_pooled_ci"] = r3(m2), [r3(lo2), r3(hi2)]
            row["G_pooled"] = r3(pooled["G"].mean())
        e_nan = sub["grounding_rate"].isna() & (sub["status"] == "ok")
        row["exams_without_grounding"] = int(e_nan.sum())
        row["vram_peak_mib_median"] = r3(np.median(peak)) if peak else None
        row["vram_model_mib_median"] = r3(np.median(model_mib)) if model_mib else None
        row["ollama_ps_vram_mib_median"] = r3(np.median([p for p in ps if p])) if ps else None
        row["llm_errors"], row["verifier_skipped"], row["parse_failures"] = llm_err, skipped, parse_fail
        # question-level judge measures
        q = qs[qs.arm == arm] if len(qs) else pd.DataFrame()
        if len(q):
            for c in ["judge_correctness", "judge_clarity", "judge_distractor_quality", "judge_bloom_fit"]:
                row[c] = r3(pd.to_numeric(q[c], errors="coerce").mean())
            wu = q["judge_would_use"].map(tf)
            row["would_use"] = r3(wu.mean())
            row["n_questions"] = len(q)
            lv = q["judge_bloom_level"].astype(str)
            row["higher_order_realized"] = r3(lv.isin(HIGHER).mean())
            if "bloom" in q and q["bloom"].notna().any() and arm not in ("E0", "E4", "B-doc-L", "B-doc-S") \
                    and not arm.startswith("E5"):
                planned = q["bloom"].astype(str)
                row["higher_order_planned"] = r3(planned.isin(HIGHER).mean())
                row["bloom_match"] = r3((planned == lv).mean())
            row["stem_len"] = r3(q["text"].astype(str).str.len().mean())
        rows[arm] = row
    return rows


def subsets(ex):
    out = {}
    for arm in sorted(ex["arm"].unique()):
        r = {}
        for src in ("hu-sajat", "hu-wiki", "en-openstax"):
            d = per_doc(ex, arm, sub=ex.source == src)
            if len(d):
                r[src] = [r3(d.mean()), len(d)]
        for L in ("short", "medium", "long"):
            d = per_doc(ex, arm, sub=ex.length == L)
            if len(d):
                r[L] = [r3(d.mean()), len(d)]
        out[arm] = r
    return out


PAIRS = [("E1", "E0", "tervezes"), ("E2", "E1", "ellenorzes"), ("E2", "E0", "teljes_modszer"),
         ("E2", "B-doc-L", "modszer_vs_teljes_dok"), ("E1", "B-doc-L", "terv_vs_teljes_dok"),
         ("E2x", "E2", "csak_szabaly_vs_E2"), ("E3", "E2", "graf"), ("E2f", "E2", "vak_proba_nelkul"),
         ("E2h", "E2", "hibrid"), ("E5a", "E0", "regi_kodolo"), ("E5b", "E0", "szoras_kuszob"),
         ("E5c", "E0", "fix_darabolas")]
FAMILY = ["tervezes", "ellenorzes", "modszer_vs_teljes_dok", "csak_szabaly_vs_E2", "graf", "teljes_modszer"]


def tests(ex):
    rows = []
    for new, ref, name in PAIRS:
        if new not in set(ex.arm) or ref not in set(ex.arm):
            continue
        a, b = per_doc(ex, ref), per_doc(ex, new)
        common = a.index.intersection(b.index)
        r = paired_wilcoxon(a.loc[common].values, b.loc[common].values)
        better = int(((b.loc[common] - a.loc[common]) > 1e-9).sum())
        worse = int(((b.loc[common] - a.loc[common]) < -1e-9).sum())
        rows.append({"name": name, "new": new, "ref": ref, "n": r["n_pairs"], "ref_Q": r3(r["mean_a"]),
                     "new_Q": r3(r["mean_b"]), "diff": r3(r["mean_diff"]), "r_rb": r3(r["r_rb"]),
                     "p": r["p"], "better_docs": better, "worse_docs": worse})
    fam = [r for r in rows if r["name"] in FAMILY]
    adj = holm([r["p"] for r in fam])
    for r, p in zip(fam, adj):
        r["p_holm"] = p
    for r in rows:
        r["p"] = None if r["p"] is None or math.isnan(r["p"]) else float(f"{r['p']:.3g}")
        if "p_holm" in r:
            r["p_holm"] = float(f"{r['p_holm']:.3g}")
    return rows


def verifier(qs, exams):
    """Verifier as classifier against the judge's grounding verdict, and rejection reasons."""
    out = {}
    if not len(qs):
        return out
    reasons = defaultdict(Counter)
    slots = defaultdict(lambda: [0, 0, 0])   # slots, first-attempt passes, attempts
    for x in exams:
        b = x.get("blueprint") or {}
        for s in b.get("slot_logs") or []:
            st = slots[x["arm"]]
            st[0] += 1
            att = s.get("attempts") or []
            st[2] += len(att)
            if att and not att[0].get("problems"):
                st[1] += 1
            for a in att:
                for p in a.get("problems") or []:
                    lab = next((k for pre, k in PROBLEM_KEYS if p.startswith(pre)), "egyeb")
                    reasons[x["arm"]][lab] += 1
    for arm in sorted(qs.arm.unique()):
        q = qs[qs.arm == arm]
        von = q["verifier_on"].map(tf) if "verifier_on" in q else pd.Series(dtype=float)
        if not len(von) or von.max() != 1.0:
            continue
        v = q["verified"].map(tf)
        g = q["grounded"].map(tf)
        mask = v.notna() & g.notna()
        v, g = v[mask], g[mask]
        tp = float(((v == 1) & (g == 1)).sum())
        r = {"n": int(len(v)), "passed_share": r3(v.mean()),
             "precision": r3(tp / (v == 1).sum()) if (v == 1).sum() else None,
             "recall": r3(tp / (g == 1).sum()) if (g == 1).sum() else None,
             "grounded_if_flagged": r3(g[v == 0].mean()) if (v == 0).sum() else None,
             "kappa": r3(cohen_kappa(list(v), list(g)))}
        st = slots.get(arm)
        if st and st[0]:
            r["first_attempt_pass"] = r3(st[1] / st[0])
            r["attempts_per_slot"] = r3(st[2] / st[0])
        r["reasons"] = dict(reasons.get(arm, {}))
        out[arm] = r
    return out


def cross_model(sets):
    """Same arm, different generator, on the documents both ran (paired by document)."""
    rows = []
    for arm in ("E0", "E1", "E2", "B-doc-L", "E2f", "E2h", "E3", "E5a", "E5b", "E5c"):
        for a, b in (("puli", "gemma"), ("qwen", "puli"), ("qwen", "gemma")):
            ea, eb = sets[a][1], sets[b][1]
            if arm not in set(ea.arm) or arm not in set(eb.arm):
                continue
            da, db = per_doc(ea, arm), per_doc(eb, arm)
            c = da.index.intersection(db.index)
            r = paired_wilcoxon(da.loc[c].values, db.loc[c].values)
            rows.append({"arm": arm, "a": a, "b": b, "n": len(c), "Q_a": r3(r["mean_a"]), "Q_b": r3(r["mean_b"]),
                         "p": None if math.isnan(r["p"]) else float(f"{r['p']:.3g}")})
    return rows


def common6(sets):
    """All three local models and the server arms on Qwen's six documents."""
    docs = sorted(sets["qwen"][1].query("arm == 'E2'")["doc_id"].unique())
    out = {"docs": docs, "table": {}}
    for key in ("qwen", "puli", "gemma"):
        ex = sets[key][1]
        for arm in sorted(ex.arm.unique()):
            d = per_doc(ex, arm)
            c = d.index.intersection(docs)
            if len(c):
                out["table"].setdefault(arm, {})[key] = [r3(d.loc[c].mean()), len(c)]
    return out


def main():
    sets = {k: load_set(k) for k in SETS}
    res = {"generated_by": "tdk/elemzes/elemzes.py", "sets": {}}
    for k, (runs, ex, qs, exams, n_infra) in sets.items():
        res["sets"][k] = {
            "model": MODEL_HU[k],
            "runs": {a: p.name for a, p in runs.items()},
            "n_documents": int(ex.doc_id.nunique()),
            "documents_by_source": {s: int(n) for s, n in ex.drop_duplicates("doc_id").source.value_counts().items()},
            "infra_errors_excluded": n_infra,
            "n_questions_judged": int(len(qs)),
            "arms": summarize(k, ex, qs, exams),
            "subsets": subsets(ex),
            "tests": tests(ex),
            "verifier": verifier(qs, exams),
            "per_doc_Q": {a: {d: r3(v) for d, v in per_doc(ex, a).items()} for a in sorted(ex.arm.unique())},
        }
    res["cross_model"] = cross_model(sets)
    res["common6"] = common6(sets)
    (OUT / "szamok.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    write_md(res)
    print("wrote", OUT / "szamok.json", "and szamok.md")


def write_md(res):
    L = ["# A dolgozat számai (generálva: tdk/elemzes/elemzes.py)", ""]
    for k, s in res["sets"].items():
        L += [f"## {s['model']} ({k}) – {s['n_documents']} dokumentum {s['documents_by_source']}, "
              f"{s['n_questions_judged']} bírált kérdés, kizárt infrastruktúra-hiba: {s['infra_errors_excluded']}", ""]
        L += ["| Kar | Q | 95% CI | F | G | A | V | Lef | Sziv | NemK | Dup | k/vizsga | min doc | <0,7 | perc | hívás | VRAM modell | would_use | magasabb rendű (terv/valós) | Bloom-egyezés |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for a, r in sorted(s["arms"].items(), key=lambda kv: -(kv[1]["Q"] or 0)):
            L.append("| " + " | ".join(str(x) for x in [
                a, r["Q"], r["ci"], r.get("format_compliant"), r.get("grounding_rate"), r.get("blind_answerability"),
                r.get("distractor_validity"), r.get("coverage"), r.get("leakage_rate"), r.get("non_question_rate"),
                r.get("duplicate_rate"), r["questions_per_exam"], r["Q_min_doc"], r["docs_below_0.7"],
                r["time_median_min"], r["calls_median"],
                f"{r['ollama_ps_vram_mib_median']} (csúcs {r['vram_peak_mib_median']})", r.get("would_use"),
                f"{r.get('higher_order_planned')}/{r.get('higher_order_realized')}", r.get("bloom_match")]) + " |")
        L += ["", "Hibák: " + ", ".join(f"{a}: sikertelen vizsga {r['failed_exams']}, LLM-hiba {r['llm_errors']}, "
                                        f"kihagyott ellenőrzés {r['verifier_skipped']}"
                                        for a, r in s["arms"].items() if r['failed_exams'] or r['llm_errors']
                                        or r['verifier_skipped']), ""]
        L += ["Részhalmazok (Q, dokumentumszám):", ""]
        for a, r in s["subsets"].items():
            L.append(f"- {a}: " + "; ".join(f"{g} {v[0]} ({v[1]})" for g, v in r.items()))
        L += ["", "Páros Wilcoxon (dokumentumonként; p_holm a 6 elemű családra):", "",
              "| összevetés | n | ref Q | új Q | Δ | r_rb | jobb/rosszabb dok | p | p_holm |", "|---|---|---|---|---|---|---|---|---|"]
        for t in s["tests"]:
            L.append(f"| {t['new']}–{t['ref']} ({t['name']}) | {t['n']} | {t['ref_Q']} | {t['new_Q']} | {t['diff']} | "
                     f"{t['r_rb']} | {t['better_docs']}/{t['worse_docs']} | {t['p']} | {t.get('p_holm', '')} |")
        L += ["", "Az ellenőrző mint osztályozó és az elutasítási okok:", ""]
        for a, v in s["verifier"].items():
            L.append(f"- {a}: {json.dumps(v, ensure_ascii=False)}")
        L.append("")
    L += ["## Modellek összevetése azonos karon (közös dokumentumok, páros Wilcoxon)", ""]
    for r in res["cross_model"]:
        L.append(f"- {r['arm']}: {r['a']} {r['Q_a']} vs {r['b']} {r['Q_b']} (n={r['n']}, p={r['p']})")
    L += ["", f"## A Qwen-futás hat dokumentumán ({', '.join(res['common6']['docs'])})", ""]
    for a, r in sorted(res["common6"]["table"].items()):
        L.append(f"- {a}: " + "; ".join(f"{k} {v[0]} ({v[1]} dok)" for k, v in r.items()))
    (OUT / "szamok.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
