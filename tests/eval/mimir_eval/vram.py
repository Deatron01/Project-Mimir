"""Peak GPU memory sampling via nvidia-smi (no-op when there is no NVIDIA GPU)."""
from __future__ import annotations

import shutil
import subprocess
import threading


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
