"""Endpoints without the embedding model or Qdrant: heavy modules are stubbed."""
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def app(monkeypatch):
    fake_torch = types.ModuleType("torch")
    fake_tf = types.ModuleType("transformers")

    class _Auto:
        @staticmethod
        def from_pretrained(*_a, **_k):
            m = types.SimpleNamespace()
            m.to = lambda *_: m
            m.eval = lambda: None
            return m

    fake_tf.AutoTokenizer = fake_tf.AutoModel = _Auto
    fake_vdb = types.ModuleType("vector_db")
    fake_vdb.RAGVectorStore = lambda **_: types.SimpleNamespace(clear_database=lambda: None)
    for name, mod in (("torch", fake_torch), ("transformers", fake_tf), ("vector_db", fake_vdb)):
        monkeypatch.setitem(sys.modules, name, mod)
    monkeypatch.setenv("GENAI_MODELS", "gpt-oss:120b,other")
    monkeypatch.setenv("OE_GENAI_API_KEY", "k")
    monkeypatch.setenv("LOCAL_ONLY", "false")
    sys.modules.pop("main", None)
    import main

    async def _no_work(*_a, **_k):   # no background generation in these tests
        return None

    monkeypatch.setattr(main, "_process_generation", _no_work)
    return main


def client(main):
    from fastapi.testclient import TestClient
    return TestClient(main.app)


def test_models_lists_server_and_local(app):
    r = client(app).get("/api/v1/models").json()
    assert [m["id"] for m in r["models"]] == ["gpt-oss:120b", "other", "local"]
    assert r["external_available"] is True and set(r["estimates_s"]) == {"external", "local"}


def test_local_only_hides_server_models_and_rejects_them(app, monkeypatch):
    monkeypatch.setattr(app, "LOCAL_ONLY", True)
    c = client(app)
    assert [m["id"] for m in c.get("/api/v1/models").json()["models"]] == ["local"]
    r = c.post("/api/v1/generate", json={"query": "q", "model": "gpt-oss:120b"})
    assert r.status_code == 400 and r.json()["detail"]["code"] == "EXTERNAL_DISABLED"


def test_generate_validates_model_and_status_has_progress(app):
    c = client(app)
    assert c.post("/api/v1/generate", json={"query": "q", "model": "nope"}).status_code == 400
    r = c.post("/api/v1/generate", json={"query": "q", "model": "local"}).json()
    assert r["location"] == "local" and r["expected_total_s"] > 0
    s = c.get(f"/api/v1/status/{r['job_id']}").json()
    assert s["status"] == "processing" and {"stage", "progress", "elapsed_s", "eta_s"} <= set(s)
    assert c.get("/api/v1/status/missing").status_code == 404
