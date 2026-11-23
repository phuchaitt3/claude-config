"""Same small job set on any machine, for comparing the laptop and the PC (issue #34).

Run it under the machine's own lock, one job per call (each job takes the lock it needs):

    python gpu_run.py run --resource ram --wait -- python bench_machine.py tests
    python gpu_run.py run --resource ram --wait -- python bench_machine.py load
    python gpu_run.py run --wait -- python bench_machine.py gpu

Add ``--smoke`` for a seconds-long form of the same steps (nothing to compare). Needs numpy,
psutil, pytest; ``gpu`` also needs torch. Prints one JSON line: wall seconds, peak RAM of the job
(and its children), GPU temperature before and after, for the report file.
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]


def gpu_temp() -> int | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout.split()
        return int(out[0])
    except Exception:
        return None


class PeakRam:
    """Peak resident memory of this process plus its children, sampled every 50 ms."""

    def __enter__(self):
        self.peak, self._stop = 0, threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)
        self._t.start()
        return self

    def _run(self):
        me = psutil.Process()
        while not self._stop.is_set():
            try:
                procs = [me, *me.children(recursive=True)]
                self.peak = max(self.peak, sum(p.memory_info().rss for p in procs if p.is_running()))
            except psutil.Error:
                pass
            time.sleep(0.05)

    def __exit__(self, *exc):
        self._stop.set()
        self._t.join()


def job_tests(smoke: bool) -> None:
    """The config repo's own scripts and hook tests, from a fixed commit (compare runs at the same HEAD)."""
    targets = ["scripts/test_merge_settings.py"] if smoke else ["scripts", "plugins/workflow/hooks"]
    subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *targets],
                   cwd=ROOT, check=False)


def job_load(smoke: bool) -> None:
    """Dataset load into RAM: 2 GB of float32 built, sorted, reduced and a CPU matrix product."""
    import numpy as np
    rng = np.random.default_rng(0)
    n = 2**20 if smoke else 2**29  # 4 MB or 2 GB of float32
    a = rng.random(n, dtype=np.float32)
    a.sort()
    m = rng.random((256, 256) if smoke else (2048, 2048), dtype=np.float32)
    for _ in range(1 if smoke else 5):
        m = (m @ m) / m.max()
    print("checksum", float(a[::1000].sum()), float(m.sum()))


def job_gpu(smoke: bool) -> None:
    """60 s of fp32 matrix products on the GPU (5 s smoke); reports TFLOPS."""
    import torch
    assert torch.cuda.is_available(), "no CUDA"
    n = 1024 if smoke else 2048
    x = torch.randn(n, n, device="cuda")
    for _ in range(5):
        x = (x @ x) / x.abs().max()
    torch.cuda.synchronize()
    seconds, steps, t0 = (5 if smoke else 60), 0, time.perf_counter()
    while time.perf_counter() - t0 < seconds:
        for _ in range(10):
            x = (x @ x) / x.abs().max()
        torch.cuda.synchronize()
        steps += 10
    dt = time.perf_counter() - t0
    print("gpu_tflops", round(steps * 2 * n**3 / dt / 1e12, 3), "device", torch.cuda.get_device_name(0))


JOBS = {"tests": job_tests, "load": job_load, "gpu": job_gpu}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("job", choices=JOBS)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    t_before = gpu_temp()
    t0 = time.perf_counter()
    peak_temp = [t_before]
    stop = threading.Event()

    def watch():
        while not stop.wait(2):
            t = gpu_temp()
            if t is not None:
                peak_temp[0] = max(peak_temp[0] or 0, t)

    threading.Thread(target=watch, daemon=True).start()
    with PeakRam() as ram:
        JOBS[args.job](args.smoke)
    wall = time.perf_counter() - t0
    stop.set()
    print(json.dumps({"bench": args.job, "smoke": args.smoke, "host": platform.node(), "wall_s": round(wall, 1),
                      "peak_ram_gb": round(ram.peak / 2**30, 2), "gpu_temp_before_c": t_before,
                      "gpu_temp_peak_c": peak_temp[0], "gpu_temp_after_c": gpu_temp(),
                      "python": platform.python_version()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
