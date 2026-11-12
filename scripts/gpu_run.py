"""gpu_run: one GPU job at a time on this machine, for any repository, and a record of who used it.

Several chats (and repositories) share one laptop GPU. Two jobs at once crash or give wrong
timings. This wrapper takes a machine-wide lock, runs the command, releases the lock when the
command ends, and appends every start, wait, refusal and end to a log, so overuse shows up in a
report instead of in a mysterious slowdown. Standard library only; no per-repository code.

    python gpu_run.py run [--wait] [--purpose TEXT] -- <command ...>   run a GPU job under the lock
    python gpu_run.py status                                            who holds the GPU now
    python gpu_run.py check                                             GPU busy with no holder?
    python gpu_run.py report [--days N]                                 usage, waits, refusals, unguarded use

The lock is an OS file lock, so it is released when the process dies and is never stale. It sits in
``$GPU_GUARD_DIR`` (default ``~/.gpu-guard``) next to ``events.jsonl``. The child process gets
``GPU_GUARD_HELD_BY=<wrapper pid>`` so a program with its own guard can see the lock is already
held for it and skip taking it again. Nothing here changes the power plan or touches credentials.
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
    return (f"{who.get('purpose', 'a job')} (pid {who.get('pid', '?')}, since "
            f"{who.get('since', '?')}, `{who.get('cmd', '?')}`, in {who.get('cwd', '?')})")


# ---------------------------------------------------------------------------------- run


def cmd_run(args: argparse.Namespace) -> int:
    command = [c for c in args.command if c != "--"] if args.command[:1] == ["--"] else args.command
    if not command:
        print("gpu_run run: no command given (put it after --)", file=sys.stderr)
        return 2
    info = {
        "pid": os.getpid(),
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
            return 3
        if not waited:
            waited = True
            log_event("waiting", purpose=info["purpose"], cwd=info["cwd"], held_by=who)
            print(f"Waiting for the GPU: held by {describe(who)}", file=sys.stderr)
        time.sleep(POLL_SECONDS)
    waited_s = round(time.time() - started_wait) if waited else 0
    log_event("start", **{k: info[k] for k in ("pid", "purpose", "cmd", "cwd")}, waited_s=waited_s)

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
    if r is None:
        print("no NVIDIA GPU readings available")
        return 0
    if Lock().is_held():
        print(f"GPU {r['util_pct']:.0f}% busy, {r['mem_mb']:.0f} MB; lock held: guarded")
        return 0
    if r["util_pct"] >= IDLE_UTIL_PCT or r["mem_mb"] >= IDLE_MEM_MB:
        log_event("unguarded", **r, processes=gpu_processes())
        print(f"UNGUARDED GPU use: {r['util_pct']:.0f}% busy, {r['mem_mb']:.0f} MB, no lock held")
        return 1
    print("GPU idle, lock free")
    return 0


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
    print(f"  UNGUARDED use seen (GPU busy, no lock held): {len(unguarded)}")
    for r in unguarded[-5:]:
        print(f"    {r['ts']}  {r.get('util_pct'):.0f}% busy, {r.get('mem_mb'):.0f} MB")
    if unguarded:
        print("  -> something used the GPU without gpu_run; find it (nvidia-smi, Task Manager).")
    elif not ends:
        print("  (no jobs recorded; run jobs through `gpu_run.py run`, and run `check` now and "
              "then, or from a hook, to catch unguarded use)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a command under the GPU lock")
    r.add_argument("--wait", action="store_true", help="queue behind the holder instead of failing")
    r.add_argument("--purpose", help="short label shown to whoever is refused (default: program)")
    r.add_argument("command", nargs=argparse.REMAINDER)
    sub.add_parser("status")
    sub.add_parser("check")
    rep = sub.add_parser("report")
    rep.add_argument("--days", type=int, default=7)
    args = p.parse_args(argv)
    return {"run": cmd_run, "status": cmd_status, "check": cmd_check, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
