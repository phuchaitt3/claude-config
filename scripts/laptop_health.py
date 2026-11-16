"""laptop_health: log what heavy runs cost this laptop, and watch slow health readings for drift.

No sensor reports wear. This script logs the things the sources tie to wear and the readings that
drift when something is going wrong, so a trend shows before a failure
(standard: findings/laptop-thermal-tiers and findings/laptop-overnight-heavy-jobs, checked 2026-11-16).
Standard library only; Windows for the snapshot sources, any OS for the report maths.

    python laptop_health.py snapshot [--label TEXT]     append one reading to health.jsonl
    python laptop_health.py report [--days N] [--swing-c C] [--heavy-pct P]
                                                        heavy hours, heat-cool cycles, GB written, trends
    python laptop_health.py reference [--minutes M] [--gpu]
                                                        the fixed cooling test (see below)
    python laptop_health.py due [--days N]              exit 1 when no reference run in N days (default 7)

Files sit in ``$GPU_GUARD_DIR`` (default ``~/.gpu-guard``): ``health.jsonl`` (snapshots and reference
results), read together with ``thermal.jsonl`` that ``gpu_run.py thermal`` writes.

What each night costs (from thermal.jsonl, derived by ``report``):
  * heavy hours: logged time with GPU utilisation or mean CPU load at or above ``--heavy-pct`` (default 80);
  * heat-cool cycles: solder joints fail by fatigue from temperature swings (Coffin-Manson), so a cycle
    is a swing of at least ``--swing-c`` (default 25 C) in the hottest component, counted with
    hysteresis so noise inside the swing is not counted. A proxy, not a lifetime figure;
  * GB written to disk: Windows' cumulative disk counter (all physical disks together), summed
    across the resets at reboot; SSD write endurance is the concern.

Slow health readings (from snapshots, one line each; a failed source is recorded as null, never raised):
  * battery design and full-charge capacity and cycle count (``powercfg /batteryreport /xml``);
  * disk health: SMART through ``smartctl`` if installed, else Windows' storage reliability counters
    (wear, temperature, power-on hours, error totals). Both need administrator rights on this laptop;
    without them the snapshot says so. ``Get-PhysicalDisk`` HealthStatus works without rights;
  * Windows hardware error events (WHEA) and unexpected-shutdown events (Kernel-Power 41), counted
    since the last snapshot: a rising count is an early sign that a component is failing.

``reference`` is the cooling check: a fixed load for M minutes (default 20): every logical CPU busy
and, with ``--gpu``, a fixed GPU matrix multiply loop (needs torch with CUDA), sampling temperature,
power and clocks. It logs the mean over the last half. Run it at the same Lenovo mode and power
setting each time, with nothing else running; a result that creeps up month after month means dust
or dried paste. It is a heavy job: start it as
``python gpu_run.py run --resource ram --wait -- python laptop_health.py reference``
(add ``--gpu`` and wrap in a second ``gpu_run.py run --wait`` for the GPU part). It is the one heavy job
that must run on the laptop (it measures the laptop), so Kaggle-first does not apply to it.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

NO_WINDOW = {"creationflags": 0x08000000} if sys.platform == "win32" else {}
ENV_DIR = "GPU_GUARD_DIR"


def guard_dir() -> Path:
    return Path(os.environ.get(ENV_DIR) or Path.home() / ".gpu-guard")


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append(name: str, record: dict) -> None:
    """Append one JSON line. Never raises: a logging problem must not stop a job."""
    try:
        d = guard_dir()
        d.mkdir(parents=True, exist_ok=True)
        with open(d / name, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now(), **record}) + "\n")
    except OSError:
        pass


def read_lines(name: str, since: datetime) -> list[dict]:
    rows: list[dict] = []
    try:
        lines = (guard_dir() / name).read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines:
        try:
            row = json.loads(line)
            if datetime.fromisoformat(row["ts"]) >= since:
                rows.append(row)
        except (ValueError, KeyError):
            continue
    return rows


# ------------------------------------------------------------------------------ derived figures


def heavy_hours(samples: list[dict], interval_s: float, heavy_pct: float = 80) -> float:
    """Hours logged with the GPU or the CPU at or above ``heavy_pct`` load."""
    n = sum(1 for r in samples if (r.get("util_pct") or 0) >= heavy_pct or (r.get("cpu_load_pct") or 0) >= heavy_pct)
    return n * interval_s / 3600


def count_cycles(temps: list[float], swing_c: float = 25.0) -> int:
    """Heat-cool cycles: a zigzag count. A swing is a move of at least ``swing_c`` from the last turning
    point (smaller wobbles are ignored); two swings, one up and one down, make a cycle."""
    if not temps:
        return 0
    swings, direction, lo, hi, ext = 0, 0, temps[0], temps[0], temps[0]
    for t in temps[1:]:
        if direction == 0:
            lo, hi = min(lo, t), max(hi, t)
            if t - lo >= swing_c:
                direction, ext, swings = 1, t, swings + 1
            elif hi - t >= swing_c:
                direction, ext, swings = -1, t, swings + 1
        elif direction == 1:
            if t > ext:
                ext = t
            elif ext - t >= swing_c:
                direction, ext, swings = -1, t, swings + 1
        else:
            if t < ext:
                ext = t
            elif t - ext >= swing_c:
                direction, ext, swings = 1, t, swings + 1
    return swings // 2


def total_with_resets(values: list[float]) -> float:
    """Sum of increases of a counter that restarts from zero at reboot: a smaller value means a reset,
    and the new value counts in full."""
    total, prev = 0.0, None
    for v in values:
        if v is None:
            continue
        if prev is not None:
            total += v - prev if v >= prev else v
        prev = v
    return total


# ----------------------------------------------------------------------------------- snapshot


def _ps(script: str, timeout: int = 60) -> str | None:
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], check=True,
                             capture_output=True, text=True, timeout=timeout, **NO_WINDOW).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return out or None


def _ps_json(script: str, timeout: int = 60):
    out = _ps(script + " | ConvertTo-Json -Compress", timeout)
    try:
        return json.loads(out) if out else None
    except ValueError:
        return None


def read_battery() -> dict | None:
    """Design and full-charge capacity (mWh) and cycle count, from Windows' battery report."""
    if sys.platform != "win32":
        return None
    path = Path(os.environ.get("TEMP", ".")) / f"health-battery-{os.getpid()}.xml"
    try:
        subprocess.run(["powercfg", "/batteryreport", "/xml", "/output", str(path)], check=True,
                       capture_output=True, timeout=60, **NO_WINDOW)
        import xml.etree.ElementTree as ET

        root = ET.parse(path).getroot()
        ns = {"b": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
        node = root.find(".//b:Battery", ns) if ns else root.find(".//Battery")
        if node is None:
            return None

        def val(tag: str):
            e = node.find(f"b:{tag}", ns) if ns else node.find(tag)
            return int(e.text) if e is not None and e.text and e.text.isdigit() else None

        return {"design_mwh": val("DesignCapacity"), "full_mwh": val("FullChargeCapacity"),
                "cycles": val("CycleCount")}
    except Exception:  # noqa: BLE001 - a health reading must never stop a job
        return None
    finally:
        try:
            path.unlink()
        except OSError:
            pass


def read_disks() -> dict:
    """Disk health: smartctl when installed, else Windows reliability counters, plus HealthStatus."""
    out: dict = {}
    health = _ps_json("Get-PhysicalDisk | Select-Object FriendlyName,MediaType,HealthStatus")
    if health:
        out["health"] = health if isinstance(health, list) else [health]
    counters = _ps_json(
        "Get-PhysicalDisk | ForEach-Object { $r = $_ | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue; "
        "[pscustomobject]@{Name=$_.FriendlyName; Wear=$r.Wear; TempC=$r.Temperature; PowerOnHours=$r.PowerOnHours; "
        "ReadErrors=$r.ReadErrorsTotal; WriteErrors=$r.WriteErrorsTotal} }")
    rows = counters if isinstance(counters, list) else ([counters] if counters else [])
    if rows and any(any(v is not None for k, v in r.items() if k != "Name") for r in rows):
        out["reliability"] = rows
    else:
        out["reliability_note"] = "no counters (needs administrator rights or smartctl)"
    try:
        smart = subprocess.run(["smartctl", "--scan"], check=False, capture_output=True, text=True, timeout=20,
                               **NO_WINDOW).stdout
        out["smartctl"] = [subprocess.run(["smartctl", "-H", "-A", line.split()[0]], check=False, capture_output=True,
                                          text=True, timeout=30, **NO_WINDOW).stdout[-3000:]
                           for line in smart.splitlines() if line.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    return out


def read_disk_bytes() -> dict | None:
    """Cumulative bytes written and read since boot, all physical disks (Windows raw counter)."""
    row = _ps_json("Get-CimInstance Win32_PerfRawData_PerfDisk_PhysicalDisk -Filter \"Name='_Total'\" | "
                   "Select-Object DiskWriteBytesPersec,DiskReadBytesPersec")
    if not row:
        return None
    return {"written_bytes": int(row["DiskWriteBytesPersec"]), "read_bytes": int(row["DiskReadBytesPersec"])}


def read_boot_time() -> str | None:
    return _ps("(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToString('o')", 30)


def count_events(since: datetime) -> dict:
    """WHEA hardware errors and Kernel-Power 41 (unexpected shutdown) since ``since``."""
    start = since.strftime("%Y-%m-%dT%H:%M:%S")
    script = (f"$s=[datetime]'{start}'; "
              "$w=(Get-WinEvent -FilterHashtable @{LogName='System';ProviderName='Microsoft-Windows-WHEA-Logger';StartTime=$s} "
              "-ErrorAction SilentlyContinue | Measure-Object).Count; "
              "$k=(Get-WinEvent -FilterHashtable @{LogName='System';Id=41;StartTime=$s} -ErrorAction SilentlyContinue | "
              "Measure-Object).Count; \"$w,$k\"")
    out = _ps(script, 120)
    try:
        w, k = out.split(",") if out else (None, None)
        return {"whea": int(w), "kernel_power_41": int(k)}
    except (ValueError, AttributeError):
        return {"whea": None, "kernel_power_41": None}


def cmd_snapshot(args: argparse.Namespace) -> int:
    since = datetime.now() - timedelta(days=30)
    previous = read_lines("health.jsonl", since.astimezone())
    last = next((r for r in reversed(previous) if r.get("event") == "snapshot"), None)
    after = datetime.fromisoformat(last["ts"]) if last else datetime.now().astimezone() - timedelta(days=1)
    rec = {"event": "snapshot", "label": args.label, "boot": read_boot_time(), "battery": read_battery(),
           "disk": read_disk_bytes(), "disks": read_disks(), "events_since_last": count_events(after.replace(tzinfo=None))}
    append("health.jsonl", rec)
    print(f"laptop_health: snapshot logged to {guard_dir() / 'health.jsonl'} "
          f"(battery {rec['battery']}, events {rec['events_since_last']})")
    return 0


# ---------------------------------------------------------------------------------- reference


def _burn(stop_at: float) -> None:
    x = 1.0001
    while time.time() < stop_at:
        for _ in range(200000):
            x = x * 1.0000001 + 1e-9


def _gpu_burn(stop_at: float) -> None:
    import torch

    a = torch.randn(4096, 4096, device="cuda", dtype=torch.float16)
    b = torch.randn(4096, 4096, device="cuda", dtype=torch.float16)
    while time.time() < stop_at:
        for _ in range(20):
            a = (a @ b).clamp_(-1, 1)
        torch.cuda.synchronize()


def cmd_reference(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(Path(__file__).parent))
    import gpu_run  # same folder: thermal and Core Temp readers

    seconds = args.minutes * 60
    stop_at = time.time() + seconds
    procs = [multiprocessing.Process(target=_burn, args=(stop_at,)) for _ in range(os.cpu_count() or 4)]
    if args.gpu:
        procs.append(multiprocessing.Process(target=_gpu_burn, args=(stop_at,)))
    for p in procs:
        p.start()
    samples = []
    try:
        while time.time() < stop_at:
            r = gpu_run.thermal_reading() or {}
            r.update(gpu_run.cpu_reading())
            samples.append(r)
            time.sleep(5)
    finally:
        for p in procs:
            p.terminate()
    tail = samples[len(samples) // 2:]  # the second half: the load has settled

    def mean(key: str):
        v = [r[key] for r in tail if r.get(key) is not None]
        return round(sum(v) / len(v), 1) if v else None

    result = {"event": "reference", "minutes": args.minutes, "gpu_load": args.gpu, "samples": len(samples),
              "cpu_temp_c": mean("cpu_temp_c"), "cpu_mhz": mean("cpu_mhz"), "gpu_temp_c": mean("gpu_temp_c"),
              "gpu_power_w": mean("power_w"), "gpu_mhz": mean("sm_mhz"),
              "cpu_temp_peak_c": max((r["cpu_temp_c"] for r in samples if r.get("cpu_temp_c") is not None), default=None)}
    append("health.jsonl", result)
    print(f"laptop_health: reference result {result}")
    return 0


def cmd_due(args: argparse.Namespace) -> int:
    since = datetime.now().astimezone() - timedelta(days=args.days)
    if any(r.get("event") == "reference" for r in read_lines("health.jsonl", since)):
        print(f"reference test done in the last {args.days} days")
        return 0
    print(f"no reference test in the last {args.days} days: run it (see `laptop_health.py` docstring)")
    return 1


# -------------------------------------------------------------------------------------- report


def cmd_report(args: argparse.Namespace) -> int:
    since = datetime.now().astimezone() - timedelta(days=args.days)
    rows = read_lines("thermal.jsonl", since - timedelta(days=30))
    interval, samples = 60.0, []
    for r in rows:
        if r.get("event") == "start" and r.get("interval_s"):
            interval = float(r["interval_s"])
        elif r.get("event") == "sample" and datetime.fromisoformat(r["ts"]) >= since:
            samples.append({**r, "_s": interval})
    print(f"Laptop health since {since.isoformat(timespec='minutes')}")
    if samples:
        hours = sum(r["_s"] for r in samples) / 3600
        hot = [max(r[k] for k in ("gpu_temp_c", "cpu_temp_c") if r.get(k) is not None)
               for r in samples if any(r.get(k) is not None for k in ("gpu_temp_c", "cpu_temp_c"))]
        print(f"  logged {hours:.1f} h; heavy (>= {args.heavy_pct:g}% load) {heavy_hours(samples, interval, args.heavy_pct):.1f} h; "
              f"heat-cool cycles (swing >= {args.swing_c:g} C): {count_cycles(hot, args.swing_c)}")
    else:
        print("  no thermal samples (start `gpu_run.py thermal` in the background)")
    snaps = [r for r in read_lines("health.jsonl", since) if r.get("event") == "snapshot"]
    if snaps:
        written = total_with_resets([(s.get("disk") or {}).get("written_bytes") for s in snaps])
        print(f"  written to disk between snapshots: {written / 1e9:.1f} GB (all disks; counter resets at reboot are handled)")
        ev = {k: sum((s.get("events_since_last") or {}).get(k) or 0 for s in snaps) for k in ("whea", "kernel_power_41")}
        print(f"  hardware errors (WHEA): {ev['whea']}   unexpected shutdowns (Kernel-Power 41): {ev['kernel_power_41']}")
        bats = [(s["ts"], s["battery"]) for s in snaps if s.get("battery") and s["battery"].get("full_mwh")]
        if bats:
            first, last = bats[0][1], bats[-1][1]
            pct = lambda b: 100 * b["full_mwh"] / b["design_mwh"] if b.get("design_mwh") else None
            print(f"  battery full charge {first['full_mwh']} -> {last['full_mwh']} mWh ({pct(last):.0f}% of design), "
                  f"cycles {first.get('cycles')} -> {last.get('cycles')}")
        notes = {(s.get("disks") or {}).get("reliability_note") for s in snaps} - {None}
        if notes:
            print(f"  disk wear / SMART: {', '.join(sorted(notes))}")
    else:
        print("  no snapshots yet (`laptop_health.py snapshot`)")
    refs = [r for r in read_lines("health.jsonl", since - timedelta(days=365)) if r.get("event") == "reference"]
    if refs:
        print("  cooling reference (CPU mean temp at clock; higher temp at the same clock means worse cooling):")
        for r in refs[-6:]:
            print(f"    {r['ts'][:10]}: CPU {r.get('cpu_temp_c')} C at {r.get('cpu_mhz')} MHz, "
                  f"GPU {r.get('gpu_temp_c')} C at {r.get('gpu_power_w')} W ({r.get('minutes')} min)")
    else:
        print("  cooling reference: none yet (`laptop_health.py due` says when to run it)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("--label", default="")
    r = sub.add_parser("report")
    r.add_argument("--days", type=int, default=1)
    r.add_argument("--swing-c", type=float, default=25.0)
    r.add_argument("--heavy-pct", type=float, default=80.0)
    ref = sub.add_parser("reference")
    ref.add_argument("--minutes", type=float, default=20.0)
    ref.add_argument("--gpu", action="store_true")
    d = sub.add_parser("due")
    d.add_argument("--days", type=int, default=7)
    args = p.parse_args(argv)
    return {"snapshot": cmd_snapshot, "report": cmd_report, "reference": cmd_reference, "due": cmd_due}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
