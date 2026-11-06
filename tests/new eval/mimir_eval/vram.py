"""GPU facts for the run record: peak memory sampling and the GPU model via nvidia-smi, and how much of
an Ollama model sits in GPU memory (all of these are no-ops without an NVIDIA GPU or Ollama)."""
from __future__ import annotations

import shutil
import subprocess
import threading

import httpx


def gpu_info() -> list[dict]:
    """Name, total memory and driver of every NVIDIA GPU; [] when there is none."""
    if shutil.which("nvidia-smi") is None:
        return []
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return []
    gpus = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 3:
            gpus.append({"name": parts[0], "memory_total_mib": int(parts[1]) if parts[1].isdigit() else None,
                         "driver": parts[2]})
    return gpus


def ollama_residency(base_url: str) -> list[dict] | None:
    """Loaded Ollama models (/api/ps) with their size and the part in GPU memory. A model that does not
    fit is split between GPU and CPU (`gpu_share` < 1), which makes it several times slower."""
    base = base_url[:-3] if base_url.endswith("/v1") else base_url
    try:
        with httpx.Client(timeout=5, trust_env=False) as c:
            models = c.get(f"{base.rstrip('/')}/api/ps").json().get("models") or []
    except Exception:
        return None
    mib = 1024 * 1024
    return [{"model": m.get("name") or m.get("model"), "size_mib": round((m.get("size") or 0) / mib),
             "vram_mib": round((m.get("size_vram") or 0) / mib),
             "gpu_share": round(m["size_vram"] / m["size"], 3) if m.get("size") else None}
            for m in models]


class VramMonitor:
    """Use as a context manager; `peak_mib` is the max used memory seen across all GPUs."""

    def __init__(self, interval_s: float = 0.5, enabled: bool = True):
        self.interval_s = interval_s
        self.enabled = enabled and shutil.which("nvidia-smi") is not None
        self.peak_mib: int | None = None
        self.baseline_mib: int | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @staticmethod
    def _sample() -> int | None:
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5).stdout
            vals = [int(v) for v in out.split() if v.strip().isdigit()]
            return max(vals) if vals else None
        except Exception:
            return None

    def _loop(self) -> None:
        while not self._stop.is_set():
            v = self._sample()
            if v is not None:
                self.peak_mib = v if self.peak_mib is None else max(self.peak_mib, v)
            self._stop.wait(self.interval_s)

    def __enter__(self) -> "VramMonitor":
        if self.enabled:
            self.baseline_mib = self._sample()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        if self._thread:
            self._stop.set()
            self._thread.join(timeout=5)
