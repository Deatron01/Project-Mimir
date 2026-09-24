"""Blueprint pipeline (E1-E3) with fake services and a scripted mock LLM."""
import json
import random
import re

import pytest

from mimir_eval import llm as llm_mod
from mimir_eval import runner as runner_mod
from mimir_eval.blueprint.graph import ConceptGraph, build_graph
from mimir_eval.blueprint.pipeline import allocate_slots, bloom_plan
from mimir_eval.blueprint.retrieval import BM25, rrf
from mimir_eval.embed import BowEmbedder
from mimir_eval.util import read_jsonl

from .test_end_to_end import FakeServices

CALLS = []


def bp_mock(messages, meta):
    system, user = messages[0]["content"], messages[-1]["content"]
    CALLS.append(system.split("]")[0].strip("["))
    rng = random.Random(len(user))
    if system.startswith("[planner]"):
        ids = sorted(set(re.findall(r"\[(C\d+)\]", user)))
        return json.dumps({"concepts": [{"concept": f"Fogalom {i}", "description": f"leírás {c}",
                                         "chunk_ids": [c], "importance": 3 - i % 3} for i, c in enumerate(ids * 3)]})
    if system.startswith("[graph]"):
        ids = re.findall(r"\[(C\d+)\] (\S+ \S+)", user)
        return json.dumps({"concepts": [{"name": f"Csomópont {c}", "definition": w, "parent": "Közös",
                                         "chunk_ids": [c]} for c, w in ids],
                           "facts": [{"text": w, "concepts": [f"Csomópont {c}"], "chunk_id": c} for c, w in ids],
                           "relations": [{"source": f"Csomópont {a[0]}", "relation": "related_to",
                                          "target": f"Csomópont {b[0]}"} for a, b in zip(ids, ids[1:])]})
    if system.startswith("[generator]"):
        concept = re.search(r"- Fogalom: (.+)", user).group(1)
        ctx = re.findall(r"\[(C\d+)\] (.+)", user.split("KONTEXTUS:")[1])
        cid, text = ctx[0]
        sent = text.split(".")[0][:70]
        retry = "HIBÁS VOLT" in user
        # every second concept is wrong on the first try (key not in the source)
        bad = (not retry) and (sum(map(ord, concept)) % 2 == 0)
        key = "Teljesen kitalált válasz" if bad else sent
        return json.dumps({"type": "mcq", "text": f"{concept}: mi igaz erre? ({sent[:30]})",
                           "answers": [{"text": key, "is_correct": True}] +
                                      [{"text": f"hamis {j} {concept}", "is_correct": False} for j in range(3)],
                           "citations": [cid], "bloom": "understand", "explanation": "x"}, ensure_ascii=False)
    if system.startswith("[verifier]"):
        src = user.split('"""')[1]
        if "marked correct" in user:
            key = re.search(r"^[A-D]\. (.+?)   <-- marked correct", user, re.M).group(1)
            return json.dumps({"key_supported": key in src, "options_wrong": [True, True, True], "ambiguous": False,
                               "problems": "" if key in src else "not in source"})
        opts = re.findall(r"^([A-D])\. (.+)$", user, re.M)
        ans = next((l for l, t in opts if t in src), "A")
        return json.dumps({"answer": ans})
    # judge (score step)
    if "exam reviewer" in system:
        if "Answer this exam question" in user:
            return json.dumps({"answer": "A"})
        return json.dumps({"key_supported": True, "distractors": [], "scores": {"correctness": 4, "clarity": 4,
                           "distractor_quality": 3, "bloom_fit": 4}, "bloom_level": "understand", "would_use": True})
    raise AssertionError(system[:40])


@pytest.fixture
def bp(tmp_path, monkeypatch):
    monkeypatch.setattr(runner_mod, "MimirServices", FakeServices)
    llm_mod.set_mock_handler(bp_mock)
    CALLS.clear()

    def cfg(name, **pipe):
        p = tmp_path / f"{name}.yaml"
        pipeline = {"kind": "blueprint", "retrieval_k": 2, "embedder": "bow", **pipe}
        p.write_text(json.dumps({"name": name, "seeds": [1], "documents": ["hu-immune", "hu-gametheory"],
                                 "exam": {"n_questions": 5, "types": ["mcq"]}, "pipeline": pipeline,
                                 "generator": {"provider": "mock", "model": "m"}, "monitor_vram": False}),
                     encoding="utf-8")
        return p
    yield tmp_path, cfg
    llm_mod.set_mock_handler(None)


def _exams(rd):
    return read_jsonl(rd / "exams.jsonl")


def test_e1_no_verifier_accepts_first_attempt(bp):
    tmp, cfg = bp
    rd = runner_mod.run_experiment(str(cfg("E1", verifier=False)), results_root=tmp / "r")
    for e in _exams(rd):
        assert e["status"] == "ok" and e["format"]["format_compliant"], e.get("error")
        assert "verifier" not in " ".join(CALLS)
        qs = e["raw_json"]["questions"]
        assert all(q["citations"] and q["context_ids"] for q in qs)
        # E1 keeps the wrong-key questions: that is what the verifier arm should fix
        assert any("kitalált" in a["text"] for q in qs for a in q["answers"] if a["is_correct"])
        assert e["llm"]["calls_by_stage"]["planner"] == 1


def test_e2_verifier_fixes_wrong_keys(bp):
    tmp, cfg = bp
    rd = runner_mod.run_experiment(str(cfg("E2", verifier=True, max_retries=2)), results_root=tmp / "r")
    for e in _exams(rd):
        assert e["status"] == "ok" and e["format"]["format_compliant"]
        qs = e["raw_json"]["questions"]
        assert not any("kitalált" in a["text"] for q in qs for a in q["answers"] if a["is_correct"])
        assert all(q["verified"] for q in qs)
        st = e["llm"]["calls_by_stage"]
        assert st["verify_grounding"] >= 5 and st["verify_blind"] >= 5 and st["generate"] > 5
        logs = e["blueprint"]["slot_logs"]
        assert any(len(l["attempts"]) > 1 for l in logs)          # at least one retry happened


def test_e3_graph_and_hybrid(bp):
    tmp, cfg = bp
    rd = runner_mod.run_experiment(str(cfg("E3", verifier=True, graph=True, retrieval="hybrid")),
                                   results_root=tmp / "r")
    for e in _exams(rd):
        assert e["status"] == "ok" and e["format"]["format_compliant"]
        assert e["blueprint"]["graph"]["concepts"] > 0
        assert "planner" not in e["llm"]["calls_by_stage"]         # graph replaces the planner call
        assert e["llm"]["calls_by_stage"]["graph"] >= 1


def test_fast_mode_skips_blind(bp):
    tmp, cfg = bp
    rd = runner_mod.run_experiment(str(cfg("E2f", verifier=True, blind_test=False)), results_root=tmp / "r")
    for e in _exams(rd):
        assert "verify_blind" not in e["llm"]["calls_by_stage"]


def test_bloom_plan_and_allocation():
    rng = random.Random(0)
    lv = bloom_plan(10, "hard", rng)
    assert len(lv) == 10 and set(lv) <= {"apply", "analyze", "evaluate"} and lv.count("analyze") == 4
    concepts = [{"concept": f"c{i}", "chunk_ids": [i % 3], "importance": 1 + i % 3} for i in range(6)]
    slots, spares = allocate_slots(concepts, 4, ["mcq", "tf"], ["remember"] * 4)
    assert {s["chunk_ids"][0] for s in slots[:3]} == {0, 1, 2}           # coverage first
    assert [s["type"] for s in slots] == ["mcq", "tf", "mcq", "tf"] and len(spares) == 2
    few, _ = allocate_slots(concepts[:2], 5, ["mcq"], ["remember"] * 5)
    assert len(few) == 5 and few[-1]["reused"]


def test_bm25_and_rrf():
    docs = ["a B-sejtek antitesteket termelnek", "a T-sejtek elpusztítják a fertőzött sejteket", "kávé pörkölés"]
    bm = BM25(docs)
    assert bm.ranking("antitest termelés")[0] == 0
    assert rrf([[0, 1, 2], [2, 0]])[0] == 0


def test_graph_merge_and_siblings():
    def ask(system, user):
        return {"concepts": [{"name": "T-sejt", "parent": "limfocita", "chunk_ids": ["C0"]},
                             {"name": "B-sejt", "parent": "limfocita", "chunk_ids": ["C1"]},
                             {"name": "B-sejtek", "parent": "limfocita", "chunk_ids": ["C1"]},
                             {"name": "makrofág", "parent": "falósejt", "chunk_ids": ["C0"]}],
                "facts": [], "relations": [{"source": "B-sejt", "relation": "used_for", "target": "antitest"}]}
    g = build_graph(["x", "y"], ask, "hu", embedder=BowEmbedder())
    assert isinstance(g, ConceptGraph)
    sib = [s.name for s in g.siblings(g.key("T-sejt"))]
    assert "B-sejt" in sib and "makrofág" not in sib
