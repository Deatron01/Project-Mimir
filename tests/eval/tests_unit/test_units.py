"""Unit tests for the parts whose numbers end up in the paper."""
import math
import random

import numpy as np
import pytest

from mimir_eval import stats
from mimir_eval.embed import BowEmbedder
from mimir_eval.metrics import coverage, duplicate_rate, retrieval_metrics
from mimir_eval.pipelines import build_query, finalize, fixed_chunks
from mimir_eval.schema import (exam_format, has_meta_reference, is_error_fallback, normalize_exam,
                               normalize_gold, parse_llm_json)
from mimir_eval.util import evidence_in

EXAM = {"title": "t", "questions": [
    {"type": "mcq", "text": "Mi termeli az antitesteket?",
     "answers": [{"text": "B-sejtek", "is_correct": True}, {"text": "T-sejtek", "is_correct": False},
                 {"text": "Makrofágok", "is_correct": False}, {"text": "Vörösvértestek", "is_correct": False}]},
    {"type": "tf", "text": "A veleszületett immunitásnak van memóriája.",
     "answers": [{"text": "Igaz", "is_correct": False}, {"text": "Hamis", "is_correct": True}]},
]}


def test_normalize_and_format():
    qs = normalize_exam(EXAM)
    assert [q["type"] for q in qs] == ["mcq", "tf"]
    assert qs[0]["key"] == "B-sejtek" and len(qs[0]["distractors"]) == 3
    f = exam_format(qs, 2, ["mcq", "tf"])
    assert f["format_compliant"] and f["count_ok"]
    assert not exam_format(qs, 3, ["mcq", "tf"])["format_compliant"]
    assert not exam_format(qs, 2, ["mcq"])["format_compliant"]     # tf not requested


def test_bad_shapes_fail():
    bad = normalize_exam({"questions": [{"type": "mcq", "text": "x?", "answers": [
        {"text": "a", "is_correct": True}, {"text": "b", "is_correct": True},
        {"text": "c", "is_correct": False}, {"text": "d", "is_correct": False}]}]})
    assert exam_format(bad, 1, ["mcq"])["shape_ok_rate"] == 0


def test_error_fallback_detected():
    fb = {"title": "Mimir AI - Generálási Hiba", "questions": [{"type": "mcq", "text": "Sajnos az AI modellek "
          "túlterheltek", "answers": [{"text": "Megértettem", "is_correct": True}]}]}
    assert is_error_fallback(fb)
    out = finalize({"raw_json": fb, "raw_text": "{}", "timings": {}})
    assert out["status"] == "fallback" and out["questions"] == []
    assert finalize({"raw_json": None, "raw_text": "garbage", "timings": {}})["status"] == "parse_error"


def test_parse_llm_json_fences():
    assert parse_llm_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_llm_json('Here: {"a": {"b": 2}} thanks') == {"a": {"b": 2}}


def test_meta_reference():
    assert has_meta_reference("A szöveg szerint mi a Nash-egyensúly?")
    assert has_meta_reference("According to the text, what is X?")
    assert has_meta_reference("Mi szerepel a dokumentumban a B-sejtekről?")
    assert not has_meta_reference("Mely sejtek termelik az antitesteket?")


def test_gold_normalisation_existing_format():
    g = normalize_gold({"kerdesek": [{"id": "q1", "kerdes": "K?", "helyes_valasz": "V", "disztraktorok": ["a", "b", "c"],
                                      "evidence": "Mondat."}]})
    assert g[0]["type"] == "mcq" and g[0]["key"] == "V" and g[0]["evidence"] == ["Mondat."]


def test_fixed_chunks_cover_text():
    text = " ".join(f"szó{i}" for i in range(500))
    ch = fixed_chunks(text, 200, 0)
    assert all(len(c["content"]) <= 200 for c in ch)
    assert " ".join(c["content"] for c in ch).split() == text.split()


def test_build_query_mentions_count_and_language():
    q = build_query(10, ["mcq"], "hard", "en")
    assert "10" in q and "angol" in q and "haladó" in q


def test_evidence_and_retrieval_metrics():
    chunks = ["A B-sejtek feladata az antitestek termelése. Más mondat.", "A T-sejtek pusztítanak.", "Egyéb."]
    assert evidence_in("A B-sejtek feladata az antitestek termelése.", chunks[0])
    gold = [{"qid": "g1", "evidence": ["A B-sejtek feladata az antitestek termelése."]},
            {"qid": "g2", "evidence": ["A T-sejtek pusztítanak."]}]
    probe = [{"gold_qid": "g1", "retrieved_idx": [0, 1, 2]}, {"gold_qid": "g2", "retrieved_idx": [2, 0, 1]}]
    m = retrieval_metrics(probe, gold, chunks)
    assert m["recall@1"] == 0.5 and m["recall@3"] == 1.0 and m["mrr"] == pytest.approx((1 + 1 / 3) / 2)


def test_duplicate_and_coverage():
    e = BowEmbedder()
    q = e.encode(["mi a nash egyensúly", "mi a nash egyensúly", "mi a pareto optimum"])
    assert duplicate_rate(q) == pytest.approx(1 / 3)
    c = e.encode(["nash egyensúly definíció", "pareto optimum fogalma", "fogolydilemma"])
    cov, nearest = coverage(q, c)
    assert cov == pytest.approx(2 / 3) and nearest == [0, 0, 1]


def test_holm():
    adj = stats.holm([0.01, 0.04, 0.03, math.nan])
    assert adj[0] == pytest.approx(0.03) and adj[2] == pytest.approx(0.06) and adj[1] == pytest.approx(0.06)
    assert math.isnan(adj[3])


def test_wilcoxon_direction_and_effect():
    rng = np.random.default_rng(1)
    a = rng.uniform(0.3, 0.6, 20)
    b = a + 0.2
    r = stats.paired_wilcoxon(a, b)
    assert r["p"] < 0.001 and r["r_rb"] == 1.0 and r["mean_diff"] == pytest.approx(0.2)
    same = stats.paired_wilcoxon(a, a)
    assert same["p"] == 1.0


def test_bootstrap_ci_contains_mean():
    m, lo, hi = stats.bootstrap_ci([0.1, 0.2, 0.3, 0.4, 0.5] * 4)
    assert lo < m < hi and m == pytest.approx(0.3)


def test_krippendorff_matches_reference_package():
    kd = pytest.importorskip("krippendorff")
    rng = random.Random(0)
    truth = [rng.randint(1, 5) for _ in range(40)]
    data = np.array([[max(1, min(5, t + rng.choice([-1, 0, 0, 1]))) for t in truth] for _ in range(3)], float)
    data[0, 3] = np.nan
    for level in ("ordinal", "interval", "nominal"):
        ours = stats.krippendorff_alpha(data, level)
        ref = kd.alpha(reliability_data=data, level_of_measurement=level)
        assert ours == pytest.approx(ref, abs=1e-9), level


def test_spearman_and_kappa():
    assert stats.spearman([1, 2, 3, 4], [2, 3, 4, 5])["rho"] == pytest.approx(1.0)
    assert stats.cohen_kappa([True, True, False, False], [True, True, False, False]) == pytest.approx(1.0)
    assert stats.cohen_kappa([True, False, True, False], [True, True, False, False]) == pytest.approx(0.0)


def test_leakage_checks():
    from mimir_eval.schema import key_in_stem, stem_is_question
    q = {"type": "mcq", "text": "A B-sejtek termelik az antitesteket, melyik sejt termeli őket?",
         "key": "A B-sejtek termelik"}
    assert key_in_stem(q) and stem_is_question(q)
    assert not key_in_stem({**q, "key": "B-sejtek"})               # too short to count as a copy
    assert not key_in_stem({**q, "type": "tf"})                     # a tf statement is its own key
    assert not stem_is_question({**q, "text": "Az antitesteket a B-sejtek termelik."})
    assert stem_is_question({**q, "text": "Válassza ki a helyes állítást:"})


def test_hardware_record(monkeypatch):
    import subprocess
    from mimir_eval import vram
    monkeypatch.setattr(vram.shutil, "which", lambda _: "/usr/bin/nvidia-smi")
    monkeypatch.setattr(vram.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a, 0, stdout="NVIDIA GeForce RTX 4060, 8188, 560.94\n"))
    assert vram.gpu_info() == [{"name": "NVIDIA GeForce RTX 4060", "memory_total_mib": 8188, "driver": "560.94"}]

    class Resp:
        def json(self):
            return {"models": [{"name": "qwen2.5:7b", "size": 6 * 2**30, "size_vram": 3 * 2**30}]}

    class Client:
        def __init__(self, **_): pass
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def get(self, url):
            assert url == "http://localhost:11434/api/ps"
            return Resp()

    monkeypatch.setattr(vram.httpx, "Client", Client)
    assert vram.ollama_residency("http://localhost:11434/v1") == [
        {"model": "qwen2.5:7b", "size_mib": 6144, "vram_mib": 3072, "gpu_share": 0.5}]
