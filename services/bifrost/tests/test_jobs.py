"""JobStore: stages, progress, ETA (no torch / Qdrant needed). Run: python -m pytest services/bifrost/tests"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jobs import DEFAULT_SECONDS, JobStore  # noqa: E402


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def test_lifecycle_keeps_old_fields():
    c = Clock()
    js = JobStore(clock=c)
    j = js.create("a", "external")
    assert j["status"] == "processing" and j["stage"] == "queued" and j["progress"] == 0
    assert j["expected_total_s"] == DEFAULT_SECONDS["external"]
    js.stage("a", "retrieving")
    js.stage("a", "generating", model="m1")
    c.t += 10
    js.complete("a", {"questions": []})
    out = js.public("a")
    assert out["status"] == "completed" and out["data"] == {"questions": []}
    assert out["progress"] == 1.0 and out["eta_s"] == 0 and out["elapsed_s"] == 10 and out["model"] == "m1"


def test_progress_follows_streamed_chars_and_eta_shrinks():
    c = Clock()
    js = JobStore(clock=c)
    js.create("a", "local")
    js.stage("a", "generating")
    c.t += 30
    js.generating("a", 875)          # a quarter of the default expected output
    first = js.public("a")
    c.t += 30
    js.generating("a", 2625)         # three quarters
    second = js.public("a")
    assert 0.15 < first["progress"] < second["progress"] < 0.92
    assert second["eta_s"] < first["eta_s"]


def test_estimate_learns_from_completed_jobs_and_ignores_fallback():
    c = Clock()
    js = JobStore(clock=c)
    for i, secs in enumerate((20, 30, 40)):
        js.create(str(i), "external")
        c.t += secs
        js.complete(str(i), {})
    assert js.expected_seconds("external") == 30
    js.create("fb", "external")
    c.t += 500
    js.complete("fb", {}, record=False)
    assert js.expected_seconds("external") == 30


def test_eta_never_zero_while_running_and_failure_and_purge():
    c = Clock()
    js = JobStore(ttl_seconds=60, clock=c)
    js.create("a", "external")
    c.t += 999                       # far over the expected time
    assert js.public("a")["eta_s"] >= 3
    js.fail("a", "boom")
    assert js.public("a")["status"] == "failed" and js.public("a")["error"] == "boom"
    c.t += 61
    js.purge_expired()
    assert js.public("a") is None and "a" not in js


def test_new_model_attempt_restarts_generating_progress():
    c = Clock()
    js = JobStore(clock=c)
    js.create("a", "external")
    js.stage("a", "generating", model="m1")
    js.generating("a", 3000)
    js.stage("a", "generating", model="local-model", location="local")
    out = js.public("a")
    assert out["progress"] == 0.15 and out["location"] == "local"
