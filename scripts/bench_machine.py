"""Same small job set on any machine, for comparing the laptop and the PC (issue #34).

Run it under the machine's own lock, one job per call (each job takes the lock it needs):

    python gpu_run.py run --resource ram --wait -- python bench_machine.py tests
    python gpu_run.py run --resource ram --wait -- python bench_machine.py load
    python gpu_run.py run --wait -- python bench_machine.py gpu
    python gpu_run.py run --wait -- python bench_machine.py model   (needs torchvision)

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


def gpu_sample() -> tuple[int | None, int | None, bool | None]:
    """(temperature C, SM clock MHz, thermal slowdown active) from one nvidia-smi call; None where unreadable."""
    for fields in ("temperature.gpu,clocks.sm,clocks_event_reasons.sw_thermal_slowdown,clocks_event_reasons.hw_thermal_slowdown",
                   "temperature.gpu,clocks.sm,clocks_throttle_reasons.sw_thermal_slowdown,clocks_throttle_reasons.hw_thermal_slowdown",
                   "temperature.gpu,clocks.sm"):
        try:
            r = subprocess.run(["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"],
                               capture_output=True, text=True, timeout=10)
            if r.returncode:
                continue
            c = [x.strip() for x in r.stdout.splitlines()[0].split(",")]
            return int(c[0]), int(c[1]), (any(x == "Active" for x in c[2:]) if len(c) > 2 else None)
        except Exception:
            continue
    return None, None, None


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


def job_model(smoke: bool) -> None:
    """ResNet-50 training steps (batch 32, 224 px, fp32, random weights and synthetic images; a real
    architecture and memory pattern, not real data): 90 s measured after warm-up (6 s smoke)."""
    import torch
    import torchvision
    assert torch.cuda.is_available(), "no CUDA"
    torch.manual_seed(0)
    model = torchvision.models.resnet50().cuda().train()
    opt = torch.optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
    x = torch.randn(32, 3, 224, 224, device="cuda")
    y = torch.randint(0, 1000, (32,), device="cuda")
    loss_fn = torch.nn.CrossEntropyLoss()

    def step():
        opt.zero_grad(set_to_none=True)
        loss_fn(model(x), y).backward()
        opt.step()

    for _ in range(3 if smoke else 10):
        step()
    torch.cuda.synchronize()
    seconds, steps, t0 = (6 if smoke else 90), 0, time.perf_counter()
    while time.perf_counter() - t0 < seconds:
        step()
        steps += 1
        if steps % 5 == 0:
            torch.cuda.synchronize()
    torch.cuda.synchronize()
    dt = time.perf_counter() - t0
    print("resnet50_train_img_per_s", round(steps * 32 / dt, 1), "peak_gpu_mem_gb",
          round(torch.cuda.max_memory_allocated() / 2**30, 2), "device", torch.cuda.get_device_name(0))


JOBS = {"tests": job_tests, "load": job_load, "gpu": job_gpu, "model": job_model}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("job", choices=JOBS)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    t_before = gpu_temp()
    t0 = time.perf_counter()
    peak_temp = [t_before]
    stop = threading.Event()

    clocks: list[int] = []
    slowdown = [False]

    def watch():
        while not stop.wait(2):
            t, clk, slow = gpu_sample()
            if t is not None:
                peak_temp[0] = max(peak_temp[0] or 0, t)
            if clk is not None:
                clocks.append(clk)
            slowdown[0] = slowdown[0] or bool(slow)

    threading.Thread(target=watch, daemon=True).start()
    with PeakRam() as ram:
        JOBS[args.job](args.smoke)
    wall = time.perf_counter() - t0
    stop.set()
    print(json.dumps({"bench": args.job, "smoke": args.smoke, "host": platform.node(), "wall_s": round(wall, 1),
                      "peak_ram_gb": round(ram.peak / 2**30, 2), "gpu_temp_before_c": t_before,
                      "gpu_temp_peak_c": peak_temp[0], "gpu_temp_after_c": gpu_temp(),
                      "sm_clock_median_mhz": sorted(clocks)[len(clocks) // 2] if clocks else None,
                      "sm_clock_min_mhz": min(clocks) if clocks else None, "thermal_slowdown_seen": slowdown[0],
                      "python": platform.python_version()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
