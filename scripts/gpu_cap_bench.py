"""gpu_cap_bench: the monthly GPU clock-cap benchmark (claude-config issue #23).

    python gpu_run.py run --wait -- python gpu_cap_bench.py [--cooling TEXT] [--model NAME]

For each setting (1200, 1350, 1500 MHz, then uncapped, in that order) it applies the cap through the
elevated scheduled tasks ``gpu-clock-cap-<mhz>`` and ``gpu-clock-cap-off`` (registered once by
``setup-machine.ps1``; no prompt at run time), runs Ollama generation back to back and stops as soon as the
run is stable: GPU temperature varies by at most 1 C over the last 60 s and tokens/s by at most 2%
(coefficient of variation) over the last 5 requests, after at least 90 s and at most 8 minutes (then it
records "not stable"). The stable window is the measurement. One ``cap_bench`` row per setting goes to
``health.jsonl``: tokens/s, mean temperature, mean power, tokens per joule, AC state, room proxy, driver,
cooling note. A run on battery power is refused. It ends with the 1350 cap on, as the overnight rule expects.
Basis: findings/gpu-benchmark-warmup-duration; the thresholds are the checker's choice from one run, to be
reviewed after the first benchmark. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import laptop_health as lh  # noqa: E402

SETTINGS = [1200, 1350, 1500, None]  # None = uncapped, in this order
TEMP_BAND_C = 1.0
TEMP_WINDOW_S = 60.0
TPS_CV_PCT = 2.0
TPS_REQUESTS = 5
MIN_S = 90.0
MAX_S = 480.0
PROMPT = "Write a long, detailed essay about the history of the printing press."


def task_for(mhz: int | None) -> str:
    return "gpu-clock-cap-off" if mhz is None else f"gpu-clock-cap-{mhz}"


def is_stable(elapsed: float, temps: list[tuple[float, float]], tps: list[float]) -> bool:
    """temps: (seconds since start, deg C); tps: tokens/s per request, oldest first."""
    if elapsed < MIN_S or len(tps) < TPS_REQUESTS:
        return False
    window = [t for s, t in temps if s >= elapsed - TEMP_WINDOW_S]
    if len(window) < 2 or max(window) - min(window) > TEMP_BAND_C:
        return False
    last = tps[-TPS_REQUESTS:]
    mean = statistics.fmean(last)
    return mean > 0 and 100 * statistics.pstdev(last) / mean <= TPS_CV_PCT


def summarise(elapsed: float, samples: list[dict], tps: list[float], stable: bool) -> dict:
    """Mean over the final 60 s window (temperature, power, clock) and the last 5 requests (tokens/s)."""
    win = [r for r in samples if r["s"] >= elapsed - TEMP_WINDOW_S]

    def mean(key: str):
        v = [r[key] for r in win if r.get(key) is not None]
        return round(statistics.fmean(v), 1) if v else None

    t_s = round(statistics.fmean(tps[-TPS_REQUESTS:]), 2) if tps else None
    power = mean("power_w")
    return {"stable": stable, "seconds": round(elapsed), "tokens_s": t_s, "temp_c": mean("gpu_temp_c"),
            "power_w": power, "sm_mhz_mean": mean("sm_mhz"),
            "sm_mhz_max": max((r["sm_mhz"] for r in win if r.get("sm_mhz") is not None), default=None),
            "tokens_per_joule": round(t_s / power, 3) if t_s and power else None}


def on_battery() -> bool:
    return lh.on_ac() is False


def driver_version() -> str | None:
    return lh.driver_version()


def generate(model: str, host: str) -> float | None:
    body = json.dumps({"model": model, "prompt": PROMPT, "stream": False, "keep_alive": "10m",
                       "options": {"num_predict": 200, "temperature": 0}}).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        d = json.load(resp)
    if not d.get("eval_duration"):
        return None
    return d["eval_count"] / (d["eval_duration"] / 1e9)


def measure(mhz: int | None, model: str, host: str) -> dict:
    import gpu_run

    task = task_for(mhz)
    subprocess.run(["schtasks", "/run", "/tn", task], check=True, capture_output=True, **lh.NO_WINDOW)
    time.sleep(5)  # the task is asynchronous
    samples: list[dict] = []
    stop = threading.Event()
    t0 = time.time()

    def sampler() -> None:
        while not stop.is_set():
            r = gpu_run.thermal_reading() or {}
            samples.append({**r, "s": time.time() - t0})
            stop.wait(2)

    th = threading.Thread(target=sampler, daemon=True)
    th.start()
    tps: list[float] = []
    stable = False
    try:
        while time.time() - t0 < MAX_S:
            v = generate(model, host)
            if v:
                tps.append(v)
            elapsed = time.time() - t0
            temps = [(r["s"], r["gpu_temp_c"]) for r in samples if r.get("gpu_temp_c") is not None]
            if is_stable(elapsed, temps, tps):
                stable = True
                break
    finally:
        stop.set()
        th.join(timeout=5)
    return summarise(time.time() - t0, samples, tps, stable)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--cooling", default=None, help="cooling setup, e.g. 'flat desk, no pad' (default: the last run's)")
    p.add_argument("--model", default=None, help="Ollama model (default: the first installed)")
    p.add_argument("--host", default="http://localhost:11434")
    args = p.parse_args(argv)
    if on_battery():
        print("gpu_cap_bench: refused: the laptop is on battery power", file=sys.stderr)
        return 2
    cooling = args.cooling or lh.last_cooling()
    if not cooling:
        print("gpu_cap_bench: no cooling note and none from an earlier run: pass --cooling", file=sys.stderr)
        return 2
    model = args.model
    if not model:
        with urllib.request.urlopen(f"{args.host}/api/tags", timeout=10) as resp:
            models = json.load(resp).get("models") or []
        if not models:
            print("gpu_cap_bench: no Ollama model installed", file=sys.stderr)
            return 2
        model = models[0]["name"]
    smart = lh.read_smart() or []
    base = {"event": "cap_bench", "bench_id": uuid.uuid4().hex[:8], "model": model, "ac": True, "cooling": cooling,
            "room_proxy_c": lh.room_proxy(smart), "driver": driver_version()}
    try:
        for mhz in SETTINGS:
            if on_battery():
                print("gpu_cap_bench: stopped: the laptop went onto battery power", file=sys.stderr)
                return 2
            row = {**base, "setting": "uncapped" if mhz is None else f"{mhz}", "clock_mhz": mhz, **measure(mhz, model, args.host)}
            lh.append("health.jsonl", row)
            print(f"gpu_cap_bench: {row}")
    finally:  # the overnight rule expects the 1350 cap on
        subprocess.run(["schtasks", "/run", "/tn", "gpu-clock-cap-on"], check=False, capture_output=True, **lh.NO_WINDOW)
    return 0


if __name__ == "__main__":
    sys.exit(main())
