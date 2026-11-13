"""gpu_run: one GPU job at a time on this machine, for any repository, and a record of who used it.

Several chats (and repositories) share one laptop GPU. Two jobs at once crash or give wrong
timings. This wrapper takes a machine-wide lock, runs the command, releases the lock when the
command ends, and appends every start, wait, refusal and end to a log, so overuse shows up in a
report instead of in a mysterious slowdown. Standard library only; no per-repository code.

    python gpu_run.py run [--wait] [--purpose TEXT] [--keep-ollama] -- <command ...>   a GPU job
    python gpu_run.py hold [--wait] [--purpose TEXT] [--keep-ollama] [--max-minutes N] -- <start command ...>
                                                     a GPU service: hold the lock until its containers stop
                                                     (with --max-minutes: `docker stop` them at the deadline)
    python gpu_run.py status                                            who holds the GPU now
    python gpu_run.py check                                             GPU busy with no holder?
    python gpu_run.py report [--days N]                                 usage, waits, refusals, unguarded use

The lock is an OS file lock, so it is released when the process dies and is never stale. It sits in
``$GPU_GUARD_DIR`` (default ``~/.gpu-guard``) next to ``events.jsonl``. The child process gets
``GPU_GUARD_HELD_BY=<wrapper pid>`` so a program with its own guard can see the lock is already
held for it and skip taking it again. Nothing here changes the power plan or touches credentials.

A GPU service (``docker run -d --gpus ...``, ``docker compose up -d`` with a GPU service) keeps the
GPU after its start command returns, so ``run`` would release the lock too early. ``hold`` runs the
start command, finds the GPU containers it started, and keeps the lock until they have all stopped
(standard: findings/shared-gpu-one-machine, checked 2026-11-13). Run it in the background; stopping
the containers (``docker stop``, ``docker compose down``) releases the lock.

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
# nvidia-smi opens no console window when the check runs from a background task (pythonw)
NO_WINDOW = {"creationflags": 0x08000000} if sys.platform == "win32" else {}


def guard_dir() -> Path:
    return Path(os.environ.get(ENV_DIR) or Path.home() / ".gpu-guard")


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


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
    def __init__(self) -> None:
        self.path = guard_dir() / "local-gpu.lock"
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
        probe = Lock()
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
    rows = smi("utilization.gpu", "memory.used")
    if not rows:
        return None
    try:
        return {"util_pct": float(rows[0][0]), "mem_mb": float(rows[0][1])}
    except ValueError:
        return None


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
    info = {
        "pid": os.getpid(),
        "kind": kind,
        "purpose": args.purpose or Path(command[0]).name,
        "cmd": " ".join(command)[:300],
        "cwd": os.getcwd(),
        "since": now(),
    }
    lock, waited, started_wait = Lock(), False, time.time()
    while not lock.try_acquire(info):
        who = lock.holder()
        if not args.wait:
            log_event("refused", **{k: info[k] for k in ("purpose", "cmd", "cwd")},
                      held_by=who)
            print(f"The local GPU is in use by {describe(who)}. Rerun with --wait to queue, or "
                  f"ask the chat that started it. (Lock: {lock.path})", file=sys.stderr)
            return None, info
        if not waited:
            waited = True
            log_event("waiting", purpose=info["purpose"], cwd=info["cwd"], held_by=who)
            print(f"Waiting for the GPU: held by {describe(who)}", file=sys.stderr)
        time.sleep(POLL_SECONDS)
    waited_s = round(time.time() - started_wait) if waited else 0
    log_event("start", **{k: info[k] for k in ("pid", "kind", "purpose", "cmd", "cwd")},
              waited_s=waited_s)
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

    peak = {"util_pct": 0.0, "mem_mb": 0.0, "n": 0}
    stop = threading.Event()

    def sample() -> None:
        while not stop.wait(SAMPLE_SECONDS):
            r = gpu_reading()
            if r:
                peak["util_pct"] = max(peak["util_pct"], r["util_pct"])
                peak["mem_mb"] = max(peak["mem_mb"], r["mem_mb"])
                peak["n"] += 1

    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    t0, code = time.time(), 1
    try:
        code = subprocess.run(command, env={**os.environ, ENV_HELD: str(os.getpid())}).returncode
    except KeyboardInterrupt:
        code = 130
    except OSError as e:
        print(f"gpu_run: cannot start {command[0]}: {e}", file=sys.stderr)
        code = 127
    finally:
        stop.set()
        lock.release()
        log_event("end", pid=info["pid"], purpose=info["purpose"], cwd=info["cwd"],
                  seconds=round(time.time() - t0), exit_code=code,
                  peak_gpu_util_pct=peak["util_pct"] or None,
                  peak_gpu_mem_mb=peak["mem_mb"] or None)
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


def cmd_status(_: argparse.Namespace) -> int:
    lock = Lock()
    if lock.is_held():
        print(f"GPU held by {describe(lock.holder())}")
    else:
        print("GPU lock is free")
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
    rows = read_events(args.days)
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


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, text in (("run", "run a command under the GPU lock"),
                       ("hold", "start GPU containers and hold the lock until they stop")):
        r = sub.add_parser(name, help=text)
        r.add_argument("--wait", action="store_true", help="queue behind the holder instead of failing")
        r.add_argument("--purpose", help="short label shown to whoever is refused (default: program)")
        r.add_argument("--keep-ollama", action="store_true",
                       help="leave Ollama's loaded models alone (default: unload them when the lock is taken)")
        r.add_argument("--stop-ollama", action="store_true", help=argparse.SUPPRESS)  # old name; now the default
        if name == "hold":
            r.add_argument("--max-minutes", type=float,
                           help="docker stop the held containers after this long, then release the lock")
        r.add_argument("command", nargs=argparse.REMAINDER)
    sub.add_parser("status")
    sub.add_parser("check")
    rep = sub.add_parser("report")
    rep.add_argument("--days", type=int, default=7)
    args = p.parse_args(argv)
    return {"run": cmd_run, "hold": cmd_hold, "status": cmd_status, "check": cmd_check,
            "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
