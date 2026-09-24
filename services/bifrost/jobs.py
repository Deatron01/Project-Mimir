"""Generálási feladatok állapota: szakasz, előrehaladás és hátralévő idő becslése.

Csak számokat és állapotot tárol (időtartam, karakterszám), a dokumentum szövegét soha.
A becslés a legutóbbi sikeres feladatok időtartamának mediánjából tanul, feldolgozási
helyenként (külső GenAI szerver vagy helyi Ollama) külön.
"""
from __future__ import annotations

import statistics
import threading
import time
from collections import deque

# Szakasz -> az előrehaladás alsó határa (0..1). A "generating" szakaszon belül a már
# legenerált karakterek aránya viszi előre a sávot.
STAGES = {"queued": 0.0, "retrieving": 0.05, "generating": 0.15, "validating": 0.92, "done": 1.0}
GENERATING_SPAN = STAGES["validating"] - STAGES["generating"]

DEFAULT_SECONDS = {"external": 60.0, "local": 150.0}
DEFAULT_OUTPUT_CHARS = 3500
HISTORY = 20


class _Rolling:
    def __init__(self, default: float):
        self.default = default
        self.values: deque[float] = deque(maxlen=HISTORY)

    def add(self, v: float) -> None:
        if v > 0:
            self.values.append(float(v))

    def median(self) -> float:
        return statistics.median(self.values) if self.values else self.default


class JobStore:
    def __init__(self, ttl_seconds: int = 3600, clock=time.time):
        self.ttl = ttl_seconds
        self.clock = clock
        self._jobs: dict[str, dict] = {}
        self._lock = threading.Lock()
        self.durations = {k: _Rolling(v) for k, v in DEFAULT_SECONDS.items()}
        self.output_chars = _Rolling(DEFAULT_OUTPUT_CHARS)

    # ------------------------------------------------------------------ lifecycle
    def create(self, job_id: str, location: str = "external") -> dict:
        self.purge_expired()
        with self._lock:
            self._jobs[job_id] = {"status": "processing", "stage": "queued", "progress": 0.0,
                                  "location": location, "model": None, "started_at": self.clock()}
        return self.public(job_id)

    def stage(self, job_id: str, stage: str, **extra) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job["stage"] = stage
            if stage == "generating":   # új modellel (újra)kezdett generálás: onnan számol
                job["progress"] = STAGES[stage]
                job["chars"] = 0
            else:
                job["progress"] = max(job["progress"], STAGES[stage])
            job.update(extra)

    def generating(self, job_id: str, chars: int) -> None:
        """Streaming közben hívva: a generált karakterek száma a várható hosszhoz képest."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job["chars"] = chars
            frac = min(0.97, chars / max(1.0, self.output_chars.median()))
            job["progress"] = max(job["progress"], STAGES["generating"] + GENERATING_SPAN * frac)

    def complete(self, job_id: str, data: dict, record: bool = True) -> None:
        """record=False: a beégetett hibaüzenet-vizsga ne torzítsa a becslést."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            if record:
                self.durations[job["location"]].add(self.clock() - job["started_at"])
                if job.get("chars"):
                    self.output_chars.add(job["chars"])
            job.update({"status": "completed", "stage": "done", "progress": 1.0, "data": data,
                        "finished_at": self.clock()})

    def fail(self, job_id: str, error: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job.update({"status": "failed", "error": error, "finished_at": self.clock()})

    def purge_expired(self) -> None:
        cutoff = self.clock() - self.ttl
        with self._lock:
            for job_id in [j for j, v in self._jobs.items() if v["started_at"] < cutoff]:
                self._jobs.pop(job_id, None)

    def __contains__(self, job_id: str) -> bool:
        return job_id in self._jobs

    # ------------------------------------------------------------------ estimates
    def expected_seconds(self, location: str) -> float:
        return self.durations[location].median()

    def eta(self, job: dict, now: float) -> float:
        if job["status"] != "processing":
            return 0.0
        elapsed = now - job["started_at"]
        expected = self.expected_seconds(job["location"])
        by_history = expected - elapsed
        p = job["progress"]
        if p >= 0.25:   # a folyamatból is lehet becsülni: átlagoljuk a kettőt
            by_rate = elapsed * (1 - p) / p
            est = by_rate if by_history <= 0 else (by_rate + by_history) / 2
        else:
            est = by_history
        return round(max(est, 3.0), 1)   # sosem mond 0-t, amíg nincs kész

    def public(self, job_id: str) -> dict | None:
        """Amit a /status visszaad. A régi mezők (status, data, error) változatlanok."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            now = job.get("finished_at", self.clock())
            elapsed = now - job["started_at"]
            out = {"status": job["status"], "stage": job["stage"], "progress": round(job["progress"], 3),
                   "elapsed_s": round(elapsed, 1), "eta_s": self.eta(job, now),
                   "expected_total_s": round(self.expected_seconds(job["location"]), 1),
                   "location": job["location"], "model": job.get("model")}
            if "data" in job:
                out["data"] = job["data"]
            if "error" in job:
                out["error"] = job["error"]
            return out

    def estimates(self) -> dict:
        return {k: round(v.median(), 1) for k, v in self.durations.items()}
