"""gpu_run: one GPU job at a time on this machine, for any repository, and a record of who used it.

Several chats (and repositories) share one laptop GPU. Two jobs at once crash or give wrong
timings. This wrapper takes a machine-wide lock, runs the command, releases the lock when the
command ends, and appends every start, wait, refusal and end to a log, so overuse shows up in a
report instead of in a mysterious slowdown. Standard library only; no per-repository code.

    python gpu_run.py run [--wait] [--purpose TEXT] [--keep-ollama] -- <command ...>   a GPU job
    python gpu_run.py run --resource ram [--wait] [--purpose TEXT] -- <command ...>   a RAM/CPU-heavy job
    python gpu_run.py hold [--wait] [--purpose TEXT] [--keep-ollama] [--max-minutes N] -- <start command ...>
                                                     a GPU service: hold the lock until its containers stop
                                                     (with --max-minutes: `docker stop` them at the deadline)
    python gpu_run.py status [--resource ram]                           who holds the GPU (or the RAM lock) now
    python gpu_run.py check                                             GPU busy with no holder?
    python gpu_run.py report [--days N] [--resource ram]                usage, waits, refusals, unguarded use
    python gpu_run.py thermal [--interval S] [--minutes M] [--purpose TEXT]
                                                     log temperatures every S seconds (no lock taken)
    python gpu_run.py report --thermal [--days N | --since ISO] [--trigger-c C]
                                                     peak and time-at-limit from the thermal log

The lock is an OS file lock, so it is released when the process dies and is never stale. It sits in
``$GPU_GUARD_DIR`` (default ``~/.gpu-guard``) next to ``events.jsonl``. The child process gets
``GPU_GUARD_HELD_BY=<wrapper pid>`` so a program with its own guard can see the lock is already
held for it and skip taking it again. Nothing here changes the power plan or touches credentials.

A GPU service (``docker run -d --gpus ...``, ``docker compose up -d`` with a GPU service) keeps the
GPU after its start command returns, so ``run`` would release the lock too early. ``hold`` runs the
start command, finds the GPU containers it started, and keeps the lock until they have all stopped
(standard: findings/shared-gpu-one-machine, checked 2026-11-13). Run it in the background; stopping
the containers (``docker stop``, ``docker compose down``) releases the lock.

A second lock, ``--resource ram``, makes RAM- or CPU-heavy jobs take turns the same way (a full test
suite, a model load into system RAM, a data build): this laptop has 16 GB, and two unattended chats
each starting one can push it into paging (standard: findings/agent-process-and-resource-control,
checked 2026-11-12: memory, not CPU, limits how many agents fit; run the heavy steps one at a time).
It is a separate lock file (``local-ram.lock``) with the same ``--wait``, queue messages and events
(each carries ``resource``); ``report --resource ram`` shows its jobs, waits and refusals. The child
gets ``GPU_GUARD_RAM_HELD_BY``. A job that needs both takes ``ram`` first and runs the GPU job inside
it (``run --resource ram -- python gpu_run.py run -- ...``), never the reverse, so two chats cannot
wait on each other. Nothing forces a job through it: whether it is a rule is the user's decision.

Ollama loads models onto the GPU on demand, outside this lock. When ``run`` or ``hold`` takes the lock
it unloads whatever Ollama has on the GPU (keep_alive 0, as Ollama's FAQ documents) and logs an
``ollama_unload`` event per model; ``--keep-ollama`` leaves them loaded and only lists them
(``--stop-ollama`` is still accepted and does nothing, since unloading is now the default). The
levers that stop Ollama taking GPU memory in the first place are settings, not this script
(standard: findings/shared-gpu-one-machine, checked 2026-11-13): ``OLLAMA_KEEP_ALIVE`` (for example
``30s``; the default is 5 minutes) shortens how long an idle model stays loaded, and
``OLLAMA_MAX_LOADED_MODELS`` (default 3 per GPU) caps how many load at once. Both are user-level
environment variables read by the Ollama server at start, so setting them needs the user's yes.
``check`` reports GPU memory that Ollama accounts for as "ollama", not as unguarded use.

``thermal`` samples GPU temperature, power, SM clock, utilisation and NVIDIA's thermal-slowdown flags
and cumulative counters, plus CPU package temperature when LibreHardwareMonitor runs and publishes
to WMI (Windows exposes no CPU temperature on its own on some laptops), and appends one line per
sample to ``thermal.jsonl``. It reads the card's own limits (target, slowdown, shutdown) from
``nvidia-smi -q`` once at start, so thresholds come from the hardware, not a generic figure
(standard: findings/laptop-thermal-tiers, checked 2026-11-14). It takes no job lock and changes no
setting; a second logger started while one runs exits at once. ``run`` also records the job's peak
GPU temperature in its ``end`` event. ``report --thermal`` gives peak and mean temperature, minutes
at or above the target and the slowdown point, thermal-slowdown time, and how many samples reached
``--trigger-c`` (default: the card's target), which is what a pause rule would have acted on.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

INFO_OFFSET = 64  # the lock is on byte 0; the holder's description starts here
POLL_SECONDS = 5
SAMPLE_SECONDS = 5
HOLD_POLL_SECONDS = 15  # how often `hold` checks that its containers still run
IDLE_UTIL_PCT = 10  # above this, or ...
IDLE_MEM_MB = 300  # ... this much memory, with no holder, is "unguarded use"
ENV_DIR = "GPU_GUARD_DIR"
ENV_HELD = "GPU_GUARD_HELD_BY"
RESOURCES = {"gpu": "local GPU", "ram": "RAM/CPU lock"}  # name -> what a refused job is told
THERMAL_FIELDS = (
    "temperature.gpu", "power.draw", "clocks.sm", "utilization.gpu",
    "clocks_event_reasons.sw_thermal_slowdown", "clocks_event_reasons.hw_thermal_slowdown",
    "clocks_event_reasons_counters.sw_thermal_slowdown", "clocks_event_reasons_counters.hw_thermal_slowdown",
)
# nvidia-smi opens no console window when the check runs from a background task (pythonw)
NO_WINDOW = {"creationflags": 0x08000000} if sys.platform == "win32" else {}


def guard_dir() -> Path:
    return Path(os.environ.get(ENV_DIR) or Path.home() / ".gpu-guard")


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def env_held(resource: str) -> str:
    """Environment variable the child of a lock holder gets: the old GPU name for gpu."""
    return ENV_HELD if resource == "gpu" else f"GPU_GUARD_{resource.upper()}_HELD_BY"


def log_event(event: str, **fields) -> None:
    """Append one JSON line. Never raises: a logging problem must not stop a job."""
    try:
        d = guard_dir()
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "events.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now(), "event": event, **fields}) + "\n")
    except OSError:
        pass


class Lock:
    def __init__(self, resource: str = "gpu") -> None:
        self.resource = resource
        self.path = guard_dir() / f"local-{resource}.lock"
        self.fd: int | None = None

    def _lock(self, fd: int) -> None:
        if sys.platform == "win32":
            import msvcrt

            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def try_acquire(self, info: dict) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT)
        try:
            self._lock(fd)
        except OSError:
            os.close(fd)
            return False
        os.ftruncate(fd, INFO_OFFSET)
        os.lseek(fd, INFO_OFFSET, os.SEEK_SET)
        os.write(fd, json.dumps(info).encode("utf-8"))
        self.fd = fd
        return True

    def update(self, info: dict) -> None:
        """Rewrite the holder's description while holding the lock."""
        if self.fd is None:
            return
        os.ftruncate(self.fd, INFO_OFFSET)
        os.lseek(self.fd, INFO_OFFSET, os.SEEK_SET)
        os.write(self.fd, json.dumps(info).encode("utf-8"))

    def release(self) -> None:
        if self.fd is None:
            return
        fd, self.fd = self.fd, None
        try:
            if sys.platform == "win32":
                import msvcrt

                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        finally:
            os.close(fd)

    def holder(self) -> dict:
        try:
            with open(self.path, "rb") as f:
                f.seek(INFO_OFFSET)
                return json.loads(f.read().decode("utf-8"))
        except (OSError, ValueError):
            return {}

    def is_held(self) -> bool:
        """True when some process holds the lock (tried and released at once)."""
        probe = Lock(self.resource)
        if probe.try_acquire({"probe": True}):
            probe.release()
            return False
        return True


def smi(*query: str) -> list[list[str]] | None:
    try:
        out = subprocess.run(
            ["nvidia-smi", f"--query-gpu={','.join(query)}", "--format=csv,noheader,nounits"],
            check=True, capture_output=True, text=True, timeout=15, **NO_WINDOW,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return [[c.strip() for c in line.split(",")] for line in out.splitlines() if line.strip()]


def gpu_reading() -> dict | None:
    rows = smi("utilization.gpu", "memory.used", "temperature.gpu")
    if not rows:
        return None
    try:
        r = {"util_pct": float(rows[0][0]), "mem_mb": float(rows[0][1])}
    except (ValueError, IndexError):
        return None
    r["temp_c"] = _num(rows[0][2]) if len(rows[0]) > 2 else None
    return r


def _num(text: str | None) -> float | None:
    try:
        return float(text)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def thermal_reading() -> dict | None:
    """One GPU sample: temperature, power, clock, load, thermal slowdown now, and the cumulative
    slowdown counters (microseconds since boot, software plus hardware thermal slowdown)."""
    rows = smi(*THERMAL_FIELDS)
    if not rows or len(rows[0]) != len(THERMAL_FIELDS):
        return None
    c = rows[0]
    counters = [_num(x) for x in c[6:8]]
    return {"gpu_temp_c": _num(c[0]), "power_w": _num(c[1]), "sm_mhz": _num(c[2]), "util_pct": _num(c[3]),
            "thermal_slowdown": any(x == "Active" for x in c[4:6]),
            "slowdown_us": None if None in counters else sum(counters)}  # type: ignore[arg-type]


def gpu_limits() -> dict:
    """The card's own limits from `nvidia-smi -q -d TEMPERATURE` (degrees C; missing ones left out)."""
    names = {"GPU Target Temperature": "target_c", "GPU Slowdown Temp": "slowdown_c",
             "GPU Shutdown Temp": "shutdown_c", "GPU Max Operating Temp": "max_operating_c"}
    try:
        out = subprocess.run(["nvidia-smi", "-q", "-d", "TEMPERATURE"], check=True, capture_output=True,
                             text=True, timeout=15, **NO_WINDOW).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    limits = {}
    for line in out.splitlines():
        key, _, val = line.partition(":")
        for prefix, name in names.items():
            if key.strip().startswith(prefix):
                v = _num(val.strip().split(" ")[0])
                if v is not None:
                    limits[name] = v
    return limits


def cpu_temp_c() -> float | None:
    """CPU package temperature from LibreHardwareMonitor's WMI provider, or None when it is not
    running (it must run as administrator to read the sensors)."""
    if sys.platform != "win32":
        return None
    ps = ("Get-CimInstance -Namespace root/LibreHardwareMonitor -ClassName Sensor -ErrorAction Stop | "
          "Where-Object { $_.SensorType -eq 'Temperature' -and $_.Name -match 'Package|Tctl|Tdie' } | "
          "Measure-Object -Property Value -Maximum | ForEach-Object { $_.Maximum }")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                             capture_output=True, text=True, timeout=20, **NO_WINDOW).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return _num(out) if out else None


def log_thermal(record: dict) -> None:
    """Append one line to thermal.jsonl. Never raises."""
    try:
        d = guard_dir()
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "thermal.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now(), **record}) + "\n")
    except OSError:
        pass


def gpu_processes() -> list[str]:
    """Compute processes nvidia-smi lists ("pid name"), to tell who used the GPU. Often empty under
    the Windows WDDM driver, which hides per-process use."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
            check=True, capture_output=True, text=True, timeout=15, **NO_WINDOW,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [" ".join(c.strip() for c in line.split(",")) for line in out.splitlines() if line.strip()]


def describe(who: dict) -> str:
    if not who:
        return "another process"
    text = (f"{who.get('purpose', 'a job')} (pid {who.get('pid', '?')}, since "
            f"{who.get('since', '?')}, `{who.get('cmd', '?')}`, in {who.get('cwd', '?')})")
    if who.get("containers"):
        text += f", containers {', '.join(who['containers'].values())}"
    return text


# ------------------------------------------------------------------------------- ollama


def _ollama_url(path: str) -> str:
    host = os.environ.get("OLLAMA_HOST") or "127.0.0.1:11434"
    if "://" not in host:
        host = "http://" + host
    host = host.replace("0.0.0.0", "127.0.0.1")
    return host.rstrip("/") + path


def ollama_models() -> list[dict]:
    """Models Ollama has loaded now: [{"name", "vram_mb"}]. Empty when Ollama is not running."""
    from urllib.request import urlopen

    try:
        with urlopen(_ollama_url("/api/ps"), timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (OSError, ValueError):
        return []
    return [{"name": m.get("name", "?"), "vram_mb": round((m.get("size_vram") or 0) / 2**20)}
            for m in data.get("models") or []]


def ollama_unload(name: str) -> bool:
    """Unload one model at once (keep_alive 0, as Ollama's FAQ documents)."""
    from urllib.request import Request, urlopen

    body = json.dumps({"model": name, "keep_alive": 0}).encode("utf-8")
    req = Request(_ollama_url("/api/generate"), data=body, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=30):
            return True
    except OSError:
        return False


def ollama_note(keep: bool) -> None:
    """Unload the models Ollama has on the GPU (the lock holder gets the GPU); with `keep`, list them."""
    models = [m for m in ollama_models() if m["vram_mb"]]
    if not models:
        return
    names = ", ".join(f"{m['name']} ({m['vram_mb']} MB)" for m in models)
    if keep:
        print(f"gpu_run: Ollama holds GPU memory outside the lock: {names} (left loaded: --keep-ollama).",
              file=sys.stderr)
        return
    failed = []
    for m in models:
        ok = ollama_unload(m["name"])
        log_event("ollama_unload", model=m["name"], vram_mb=m["vram_mb"], ok=ok)
        if not ok:
            failed.append(m["name"])
    print(f"gpu_run: unloaded Ollama models: {names}", file=sys.stderr)
    if failed:
        print(f"gpu_run: could not unload {', '.join(failed)}; they still hold GPU memory.", file=sys.stderr)


def classify(reading: dict | None, locked: bool, ollama_mb: float) -> str:
    """'none' (no readings), 'guarded', 'idle', 'ollama' (busy, but Ollama accounts for the memory),
    or 'unguarded'."""
    if reading is None:
        return "none"
    if locked:
        return "guarded"
    busy = reading["util_pct"] >= IDLE_UTIL_PCT or reading["mem_mb"] >= IDLE_MEM_MB
    if not busy:
        return "idle"
    if ollama_mb and reading["mem_mb"] - ollama_mb < IDLE_MEM_MB:
        return "ollama"
    return "unguarded"


# ------------------------------------------------------------------------------- docker


def gpu_containers() -> dict[str, str] | None:
    """Running containers that requested a GPU, {id: name}; None when Docker cannot be asked."""
    try:
        ids = subprocess.run(["docker", "ps", "-q", "--no-trunc"], check=True, capture_output=True,
                             text=True, timeout=30, **NO_WINDOW).stdout.split()
        if not ids:
            return {}
        out = subprocess.run(
            ["docker", "inspect", "--format",
             "{{.Id}} {{.Name}} {{json .HostConfig.DeviceRequests}}", *ids],
            check=True, capture_output=True, text=True, timeout=30, **NO_WINDOW,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    found = {}
    for line in out.splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3 and "gpu" in parts[2].lower():
            found[parts[0]] = parts[1].lstrip("/")
    return found


# ---------------------------------------------------------------------------------- run


def _command(args: argparse.Namespace) -> list[str]:
    return [c for c in args.command if c != "--"] if args.command[:1] == ["--"] else args.command


def acquire(args: argparse.Namespace, command: list[str], kind: str) -> tuple[Lock | None, dict]:
    """Take the lock (queueing with --wait); log start. (None, info) when refused."""
    res = getattr(args, "resource", "gpu")
    info = {
        "resource": res,
        "pid": os.getpid(),
        "kind": kind,
        "purpose": args.purpose or Path(command[0]).name,
        "cmd": " ".join(command)[:300],
        "cwd": os.getcwd(),
        "since": now(),
    }
    lock, waited, started_wait = Lock(res), False, time.time()
    while not lock.try_acquire(info):
        who = lock.holder()
        if not args.wait:
            log_event("refused", resource=res, **{k: info[k] for k in ("purpose", "cmd", "cwd")},
                      held_by=who)
            print(f"The {RESOURCES[res]} is in use by {describe(who)}. Rerun with --wait to queue, or "
                  f"ask the chat that started it. (Lock: {lock.path})", file=sys.stderr)
            return None, info
        if not waited:
            waited = True
            log_event("waiting", resource=res, purpose=info["purpose"], cwd=info["cwd"], held_by=who)
            print(f"Waiting for the {RESOURCES[res]}: held by {describe(who)}", file=sys.stderr)
        time.sleep(POLL_SECONDS)
    waited_s = round(time.time() - started_wait) if waited else 0
    log_event("start", **{k: info[k] for k in ("resource", "pid", "kind", "purpose", "cmd", "cwd")},
              waited_s=waited_s)
    if res == "gpu":
        ollama_note(getattr(args, "keep_ollama", False))
    return lock, info


def cmd_run(args: argparse.Namespace) -> int:
    command = _command(args)
    if not command:
        print("gpu_run run: no command given (put it after --)", file=sys.stderr)
        return 2
    lock, info = acquire(args, command, "job")
    if lock is None:
        return 3
    res = info["resource"]

    peak = {"util_pct": 0.0, "mem_mb": 0.0, "temp_c": 0.0, "n": 0}
    stop = threading.Event()

    def sample() -> None:
        while not stop.wait(SAMPLE_SECONDS):
            r = gpu_reading()
            if r:
                peak["util_pct"] = max(peak["util_pct"], r["util_pct"])
                peak["mem_mb"] = max(peak["mem_mb"], r["mem_mb"])
                peak["temp_c"] = max(peak["temp_c"], r.get("temp_c") or 0.0)
                peak["n"] += 1

    if res == "gpu":  # GPU readings only make sense for the GPU lock
        threading.Thread(target=sample, daemon=True).start()
    t0, code = time.time(), 1
    try:
        code = subprocess.run(command, env={**os.environ, env_held(res): str(os.getpid())}).returncode
    except KeyboardInterrupt:
        code = 130
    except OSError as e:
        print(f"gpu_run: cannot start {command[0]}: {e}", file=sys.stderr)
        code = 127
    finally:
        stop.set()
        lock.release()
        log_event("end", resource=res, pid=info["pid"], purpose=info["purpose"], cwd=info["cwd"],
                  seconds=round(time.time() - t0), exit_code=code,
                  peak_gpu_util_pct=peak["util_pct"] or None,
                  peak_gpu_mem_mb=peak["mem_mb"] or None,
                  peak_gpu_temp_c=peak["temp_c"] or None)
    return code


def stop_containers(ids: list[str]) -> bool:
    """`docker stop` by id: the client-side deadline that `timeout docker run` cannot give
    (standard: findings/docker-run-timeout-cleanup, checked 2026-11-13)."""
    try:
        subprocess.run(["docker", "stop", *ids], check=True, capture_output=True, timeout=120, **NO_WINDOW)
    except (OSError, subprocess.SubprocessError):
        return False
    return True


def cmd_hold(args: argparse.Namespace) -> int:
    """Run a start command that leaves GPU containers running; hold the lock until they stop."""
    command = _command(args)
    if not command:
        print("gpu_run hold: no command given (put it after --)", file=sys.stderr)
        return 2
    lock, info = acquire(args, command, "service")
    if lock is None:
        return 3
    t0, code, held = time.time(), 1, {}
    try:
        before = gpu_containers() or {}
        try:
            code = subprocess.run(command, env={**os.environ, ENV_HELD: str(os.getpid())},
                                  check=False).returncode
        except OSError as e:
            print(f"gpu_run: cannot start {command[0]}: {e}", file=sys.stderr)
            code = 127
        after = gpu_containers()
        if after is None:
            print("gpu_run hold: cannot list Docker containers; releasing the lock.", file=sys.stderr)
            return code
        held = {cid: name for cid, name in after.items() if cid not in before}
        if not held:
            print("gpu_run hold: the command left no new GPU container running; lock released.",
                  file=sys.stderr)
            return code
        lock.update({**info, "containers": held})
        log_event("hold", pid=info["pid"], purpose=info["purpose"], cwd=info["cwd"],
                  containers=sorted(held.values()))
        deadline = t0 + args.max_minutes * 60 if getattr(args, "max_minutes", None) else None
        until = f" (deadline: {args.max_minutes} min, then `docker stop`)" if deadline else ""
        print(f"gpu_run hold: holding the GPU lock while {', '.join(held.values())} run; stop them "
              f"to release it{until}.", file=sys.stderr, flush=True)
        while True:
            time.sleep(HOLD_POLL_SECONDS)
            running = gpu_containers()
            if running is not None and not set(held) & set(running):
                break
            if deadline and time.time() >= deadline:
                ok = stop_containers(list(held))
                log_event("deadline", pid=info["pid"], purpose=info["purpose"],
                          containers=sorted(held.values()), stopped=ok)
                print(f"gpu_run hold: deadline reached; stopped {', '.join(held.values())}.",
                      file=sys.stderr)
                code = 124  # what `timeout` returns
                break
        return code
    except KeyboardInterrupt:
        return 130
    finally:
        lock.release()
        log_event("end", pid=info["pid"], kind="service", purpose=info["purpose"], cwd=info["cwd"],
                  seconds=round(time.time() - t0), exit_code=code,
                  containers=sorted(held.values()) or None)


# ----------------------------------------------------------------------------- status, check


def cmd_status(args: argparse.Namespace) -> int:
    res = getattr(args, "resource", "gpu")
    lock = Lock(res)
    name = "GPU" if res == "gpu" else res.upper()
    if lock.is_held():
        print(f"{name} held by {describe(lock.holder())}")
    else:
        print(f"{name} lock is free")
    return 0


def cmd_check(_: argparse.Namespace) -> int:
    """Exit 1 and log ``unguarded`` when the GPU is busy but nobody holds the lock."""
    r = gpu_reading()
    locked = r is not None and Lock().is_held()
    models = ollama_models() if r is not None and not locked else []
    ollama_mb = sum(m["vram_mb"] for m in models)
    state = classify(r, locked, ollama_mb)
    if state == "none":
        print("no NVIDIA GPU readings available")
        return 0
    if state == "guarded":
        print(f"GPU {r['util_pct']:.0f}% busy, {r['mem_mb']:.0f} MB; lock held: guarded")
        return 0
    if state == "idle":
        print("GPU idle, lock free")
        return 0
    if state == "ollama":
        log_event("ollama", **r, models=[m["name"] for m in models], ollama_mb=ollama_mb)
        print(f"GPU {r['util_pct']:.0f}% busy, {r['mem_mb']:.0f} MB: Ollama's loaded models "
              f"({', '.join(m['name'] for m in models)}), outside the lock")
        return 0
    containers = gpu_containers() or {}
    log_event("unguarded", **r, processes=gpu_processes(), containers=sorted(containers.values()),
              ollama_mb=ollama_mb or None)
    extra = f"; GPU containers: {', '.join(containers.values())}" if containers else ""
    print(f"UNGUARDED GPU use: {r['util_pct']:.0f}% busy, {r['mem_mb']:.0f} MB, no lock held{extra}")
    return 1


# --------------------------------------------------------------------------------- report


def cmd_thermal(args: argparse.Namespace) -> int:
    """Log temperatures until stopped (Ctrl+C, process killed) or --minutes have passed."""
    single = Lock("thermal")
    if not single.try_acquire({"pid": os.getpid(), "purpose": args.purpose or "thermal", "since": now()}):
        who = single.holder()
        print(f"gpu_run thermal: a logger already runs (pid {who.get('pid')}, {who.get('purpose')}); "
              "its log is shared, nothing to do")
        return 0
    limits = gpu_limits()
    log_thermal({"event": "start", "pid": os.getpid(), "purpose": args.purpose or "thermal",
                 "interval_s": args.interval, "limits": limits})
    print(f"gpu_run thermal: logging every {args.interval:g} s to {guard_dir() / 'thermal.jsonl'}; "
          f"card limits {limits or 'unknown'}", flush=True)
    deadline = time.time() + args.minutes * 60 if args.minutes else None
    n = 0
    try:
        while deadline is None or time.time() < deadline:
            r = thermal_reading() or {}
            r["cpu_temp_c"] = cpu_temp_c()
            log_thermal({"event": "sample", **r})
            n += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        log_thermal({"event": "end", "pid": os.getpid(), "samples": n})
        single.release()
    return 0


def read_thermal(since: datetime) -> list[dict]:
    rows: list[dict] = []
    try:
        lines = (guard_dir() / "thermal.jsonl").read_text(encoding="utf-8").splitlines()
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


def report_thermal(args: argparse.Namespace) -> int:
    since = datetime.fromisoformat(args.since) if args.since else datetime.now() - timedelta(days=args.days)
    if since.tzinfo is None:
        since = since.astimezone()
    rows = read_thermal(since)
    starts = [r for r in rows if r.get("event") == "start"]
    samples = [r for r in rows if r.get("event") == "sample" and r.get("gpu_temp_c") is not None]
    limits = next((s["limits"] for s in reversed(starts) if s.get("limits")), None) or gpu_limits()
    interval = next((s["interval_s"] for s in reversed(starts) if s.get("interval_s")), 60)
    print(f"Temperatures since {since.isoformat(timespec='minutes')} ({guard_dir() / 'thermal.jsonl'})")
    print(f"  card limits: {limits or 'unknown'}")
    if not samples:
        print("  (no samples; start `gpu_run.py thermal` in the background)")
        return 0
    temps = [r["gpu_temp_c"] for r in samples]
    target, slow = limits.get("target_c"), limits.get("slowdown_c")
    trigger = args.trigger_c if args.trigger_c is not None else target

    def minutes(threshold: float | None) -> str:
        return "n/a" if threshold is None else f"{sum(t >= threshold for t in temps) * interval / 60:.0f} min"

    slowdown_s, prev = 0.0, None
    for r in samples:  # the counters reset at reboot: add only positive steps
        cur = r.get("slowdown_us")
        if cur is not None and prev is not None and cur > prev:
            slowdown_s += (cur - prev) / 1e6
        if cur is not None:
            prev = cur
    powers = [r["power_w"] for r in samples if r.get("power_w") is not None]
    cpus = [r["cpu_temp_c"] for r in samples if r.get("cpu_temp_c") is not None]
    print(f"  samples: {len(samples)} (every {interval:g} s)   GPU peak {max(temps):.0f} C   "
          f"mean {sum(temps) / len(temps):.0f} C   peak power {max(powers, default=0):.0f} W")
    print(f"  at or above target ({target} C): {minutes(target)}   "
          f"at or above slowdown ({slow} C): {minutes(slow)}")
    print(f"  thermal slowdown: {slowdown_s:.0f} s by the counters, "
          f"{sum(1 for r in samples if r.get('thermal_slowdown'))} samples with it active")
    if trigger is not None:
        hits = [r for r in samples if r["gpu_temp_c"] >= trigger]
        print(f"  samples at or above the trigger {trigger:g} C (what a pause rule would act on): {len(hits)}"
              + (f", first {hits[0]['ts']}" if hits else ""))
    print("  CPU package: " + (f"peak {max(cpus):.0f} C, mean {sum(cpus) / len(cpus):.0f} C" if cpus
                               else "not read (LibreHardwareMonitor not running as administrator)"))
    return 0


def read_events(days: int) -> list[dict]:
    path, cutoff, rows = guard_dir() / "events.jsonl", datetime.now().astimezone() - timedelta(days=days), []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines:
        try:
            row = json.loads(line)
            if datetime.fromisoformat(row["ts"]) >= cutoff:
                rows.append(row)
        except (ValueError, KeyError):
            continue
    return rows


def cmd_report(args: argparse.Namespace) -> int:
    if getattr(args, "thermal", False):
        return report_thermal(args)
    res = getattr(args, "resource", "gpu")
    rows = [r for r in read_events(args.days) if r.get("resource", "gpu") == res]
    if res != "gpu":
        return report_lock(args, rows, res)
    ends = [r for r in rows if r["event"] == "end"]
    starts = [r for r in rows if r["event"] == "start"]
    refused = [r for r in rows if r["event"] == "refused"]
    waited = [r for r in starts if r.get("waited_s")]
    unguarded = [r for r in rows if r["event"] == "unguarded"]
    total = sum(r.get("seconds", 0) for r in ends)
    print(f"GPU use, last {args.days} day(s) ({guard_dir() / 'events.jsonl'})")
    print(f"  jobs run: {len(ends)}   GPU time: {total / 3600:.1f} h   "
          f"failed: {sum(1 for r in ends if r.get('exit_code'))}")
    by_dir: dict[str, float] = {}
    for r in ends:
        by_dir[r["cwd"]] = by_dir.get(r["cwd"], 0) + r.get("seconds", 0)
    for cwd, sec in sorted(by_dir.items(), key=lambda kv: -kv[1])[:8]:
        print(f"    {sec / 3600:5.1f} h  {cwd}")
    print(f"  refused (GPU taken, did not wait): {len(refused)}")
    for r in refused[-5:]:
        print(f"    {r['ts']}  {r.get('purpose')} in {r.get('cwd')} -> held by "
              f"{(r.get('held_by') or {}).get('purpose', '?')}")
    print(f"  queued (waited for the GPU): {len(waited)}   "
          f"longest wait: {max((r['waited_s'] for r in waited), default=0)} s")
    holds = [r for r in ends if r.get("kind") == "service"]
    print(f"  services held (GPU containers kept the lock): {len(holds)}   "
          f"time: {sum(r.get('seconds', 0) for r in holds) / 3600:.1f} h")
    ollama = [r for r in rows if r["event"] == "ollama"]
    print(f"  Ollama models seen on the GPU outside the lock: {len(ollama)}   "
          f"unloaded at lock take: {sum(1 for r in rows if r['event'] == 'ollama_unload' and r.get('ok'))}")
    print(f"  UNGUARDED use seen (GPU busy, no lock held): {len(unguarded)}")
    for r in unguarded[-5:]:
        who = f"  containers: {', '.join(r['containers'])}" if r.get("containers") else ""
        print(f"    {r['ts']}  {r.get('util_pct'):.0f}% busy, {r.get('mem_mb'):.0f} MB{who}")
    if unguarded:
        print("  -> something used the GPU without gpu_run; find it (nvidia-smi, Task Manager).")
    elif not ends:
        print("  (no jobs recorded; run jobs through `gpu_run.py run`, and run `check` now and "
              "then, or from a hook, to catch unguarded use)")
    return 0


def report_lock(args: argparse.Namespace, rows: list[dict], res: str) -> int:
    """Usage report for a lock other than the GPU's: jobs, time, waits and refusals."""
    ends = [r for r in rows if r["event"] == "end"]
    refused = [r for r in rows if r["event"] == "refused"]
    waited = [r for r in rows if r["event"] == "start" and r.get("waited_s")]
    print(f"{RESOURCES[res]} use, last {args.days} day(s) ({guard_dir() / 'events.jsonl'})")
    print(f"  jobs run: {len(ends)}   time: {sum(r.get('seconds', 0) for r in ends) / 3600:.1f} h   "
          f"failed: {sum(1 for r in ends if r.get('exit_code'))}")
    by_dir: dict[str, float] = {}
    for r in ends:
        by_dir[r["cwd"]] = by_dir.get(r["cwd"], 0) + r.get("seconds", 0)
    for cwd, sec in sorted(by_dir.items(), key=lambda kv: -kv[1])[:8]:
        print(f"    {sec / 3600:5.1f} h  {cwd}")
    print(f"  refused (lock taken, did not wait): {len(refused)}")
    for r in refused[-5:]:
        print(f"    {r['ts']}  {r.get('purpose')} in {r.get('cwd')} -> held by "
              f"{(r.get('held_by') or {}).get('purpose', '?')}")
    print(f"  queued (waited for the lock): {len(waited)}   "
          f"longest wait: {max((r['waited_s'] for r in waited), default=0)} s")
    if not ends:
        print(f"  (no jobs recorded; run heavy jobs through `gpu_run.py run --resource {res}`)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, text in (("run", "run a command under the GPU lock"),
                       ("hold", "start GPU containers and hold the lock until they stop")):
        r = sub.add_parser(name, help=text)
        if name == "run":
            r.add_argument("--resource", choices=sorted(RESOURCES), default="gpu",
                           help="which lock: gpu (default) or ram (RAM/CPU-heavy jobs)")
        r.add_argument("--wait", action="store_true", help="queue behind the holder instead of failing")
        r.add_argument("--purpose", help="short label shown to whoever is refused (default: program)")
        r.add_argument("--keep-ollama", action="store_true",
                       help="leave Ollama's loaded models alone (default: unload them when the lock is taken)")
        r.add_argument("--stop-ollama", action="store_true", help=argparse.SUPPRESS)  # old name; now the default
        if name == "hold":
            r.add_argument("--max-minutes", type=float,
                           help="docker stop the held containers after this long, then release the lock")
        r.add_argument("command", nargs=argparse.REMAINDER)
    st = sub.add_parser("status")
    st.add_argument("--resource", choices=sorted(RESOURCES), default="gpu")
    sub.add_parser("check")
    rep = sub.add_parser("report")
    rep.add_argument("--days", type=int, default=7)
    rep.add_argument("--resource", choices=sorted(RESOURCES), default="gpu")
    rep.add_argument("--thermal", action="store_true", help="report the thermal log instead of GPU use")
    rep.add_argument("--since", help="thermal report: start time (ISO, e.g. 2026-11-14T21:30)")
    rep.add_argument("--trigger-c", type=float,
                     help="thermal report: count samples at or above this (default: the card's target)")
    th = sub.add_parser("thermal", help="log temperatures every --interval seconds")
    th.add_argument("--interval", type=float, default=60)
    th.add_argument("--minutes", type=float, help="stop after this long (default: run until stopped)")
    th.add_argument("--purpose", help="label for the log (default: thermal)")
    args = p.parse_args(argv)
    return {"run": cmd_run, "hold": cmd_hold, "status": cmd_status, "check": cmd_check,
            "report": cmd_report, "thermal": cmd_thermal}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
