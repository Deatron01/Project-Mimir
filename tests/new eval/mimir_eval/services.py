"""Thin HTTP client for the Mimir microservices (ports from docker-compose.yml)."""
from __future__ import annotations

import mimetypes
import time

import httpx


class ServiceError(RuntimeError):
    pass


class MimirServices:
    def __init__(self, wellspring: str, runecarver: str, bifrost: str, timeout_s: float = 600,
                 poll_interval_s: float = 2.0, **_):
        self.urls = {"wellspring": wellspring.rstrip("/"), "runecarver": runecarver.rstrip("/"),
                     "bifrost": bifrost.rstrip("/")}
        self.timeout_s = timeout_s
        self.poll_interval_s = poll_interval_s
        self._http = httpx.Client(timeout=timeout_s, trust_env=False)

    def close(self) -> None:
        self._http.close()

    def _post(self, service: str, path: str, **kw) -> tuple[dict, float]:
        t0 = time.perf_counter()
        r = self._http.post(f"{self.urls[service]}{path}", **kw)
        dt = time.perf_counter() - t0
        if r.status_code != 200:
            raise ServiceError(f"{service}{path} -> HTTP {r.status_code}: {r.text[:300]}")
        return r.json(), dt

    def health(self) -> dict:
        out = {}
        for name, base in self.urls.items():
            try:
                r = self._http.get(f"{base}/health", timeout=5)
                out[name] = "ok" if r.status_code == 200 else f"HTTP {r.status_code}"
            except Exception as e:  # connection refused etc.
                out[name] = f"down ({type(e).__name__})"
        return out

    # --- pipeline steps -------------------------------------------------
    def extract(self, filename: str, data: bytes) -> tuple[str, float]:
        mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        res, dt = self._post("wellspring", "/api/v1/extract", files={"file": (filename, data, mime)})
        return res.get("content", ""), dt

    def chunk(self, filename: str, extension: str, text: str, *, method: str = "percentile",
              threshold: float | None = None, target_size: int = 1000,
              encoder: str = "window") -> tuple[list[dict], float]:
        body = {"filename": filename, "extension": extension, "content": text,
                "target_size": target_size, "method": method, "encoder": encoder}
        if threshold is not None:
            body["threshold_val"] = threshold
            if method == "percentile":
                body["percentile"] = threshold      # older RuneCarver builds only read this
        res, dt = self._post("runecarver", "/api/v1/chunk", json=body)
        return res.get("chunks", []), dt

    def ingest(self, chunks: list[dict]) -> tuple[dict, float]:
        return self._post("bifrost", "/api/v1/ingest", json={"chunks": chunks})

    def search(self, query: str, limit: int) -> tuple[list[dict], float]:
        res, dt = self._post("bifrost", "/api/v1/search", json={"query": query, "limit": limit})
        return res.get("results", []), dt

    def generate(self, query: str, limit: int, fmt: str = "json") -> tuple[dict, float]:
        """Start a Bifrost job and poll until done. Returns the job record and wall time."""
        t0 = time.perf_counter()
        res, _ = self._post("bifrost", "/api/v1/generate", json={"query": query, "limit": limit, "format": fmt})
        job_id = res.get("job_id")
        if not job_id:  # very old Bifrost answered synchronously
            return {"status": "completed", "data": res.get("data", {})}, time.perf_counter() - t0
        while True:
            if time.perf_counter() - t0 > self.timeout_s:
                raise ServiceError(f"bifrost job {job_id} timed out after {self.timeout_s}s")
            r = self._http.get(f"{self.urls['bifrost']}/api/v1/status/{job_id}")
            if r.status_code != 200:
                raise ServiceError(f"bifrost status -> HTTP {r.status_code}: {r.text[:300]}")
            job = r.json()
            if job.get("status") in ("completed", "failed"):
                return job, time.perf_counter() - t0
            time.sleep(self.poll_interval_s)
