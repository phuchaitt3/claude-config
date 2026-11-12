"""UserPromptSubmit hook: tell the chat when the machine is short of memory or CPU.

`gpu_watch.py` covers the GPU. This covers the rest of a shared laptop: a chat that starts a heavy
local job (a big test run, a data build, a model load into system RAM) while memory is nearly gone
or the CPU is saturated slows every other chat and can crash the machine (standard:
standards/agent-process-and-resource-control, checked 2026-11-12). The hook samples at most once
every two minutes, using two Windows API calls (no subprocess), and tells the chat in one line when
free memory is low or the CPU averaged high since the last sample. At most one line per ten minutes
while the load lasts. It never blocks or kills anything. Silent when the machine is fine, on other
platforms, and on any error: a broken hook must never block a session.
"""

from __future__ import annotations

import ctypes
import json
import sys
import time
from ctypes import wintypes
from pathlib import Path

CACHE = Path.home() / ".claude" / "hook-cache" / "load_watch.json"
CHECK_EVERY_S = 120
TELL_EVERY_S = 600
LOW_FREE_MB = 2048
LOW_FREE_PCT = 12.0
HIGH_CPU_PCT = 85.0


def decide(state: dict, now: float, free_mb: float, total_mb: float, cpu_pct: float | None) -> tuple[dict, str]:
    """(new state, text for the chat); text is empty when the machine is fine or already told."""
    state = dict(state, checked=now)
    problems = []
    if free_mb < LOW_FREE_MB or free_mb / total_mb * 100 < LOW_FREE_PCT:
        problems.append(f"free memory {free_mb / 1024:.1f} GB of {total_mb / 1024:.0f} GB")
    if cpu_pct is not None and cpu_pct >= HIGH_CPU_PCT:
        problems.append(f"CPU {cpu_pct:.0f}% busy over the last {CHECK_EVERY_S // 60} minutes")
    if not problems or now - state.get("told", 0) < TELL_EVERY_S:
        return state, ""
    state["told"] = now
    text = (
        "machine load is high (" + "; ".join(problems) + "). Do not start a heavy local job "
        "(inference, a full test run, a data build, a large model load) now: it would slow every "
        "other chat and can crash the laptop. Say so to the user, run it later or on Kaggle, and "
        "ask other chats what they are running if the cause is unknown."
    )
    return state, text


class _MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def memory_mb() -> tuple[float, float]:
    """(available, total) physical memory in MB."""
    status = _MemoryStatus()
    status.dwLength = ctypes.sizeof(_MemoryStatus)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))  # type: ignore[attr-defined]
    return status.ullAvailPhys / 2**20, status.ullTotalPhys / 2**20


def cpu_times() -> tuple[int, int]:
    """(busy, total) system CPU time in 100 ns ticks since boot."""
    idle, kernel, user = (wintypes.FILETIME() for _ in range(3))
    ctypes.windll.kernel32.GetSystemTimes(  # type: ignore[attr-defined]
        ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
    )

    def value(t: wintypes.FILETIME) -> int:
        return (t.dwHighDateTime << 32) | t.dwLowDateTime

    total = value(kernel) + value(user)  # kernel time includes idle time
    return total - value(idle), total


def cpu_percent(previous: list[int] | None, current: tuple[int, int]) -> float | None:
    if not previous or current[1] <= previous[1]:
        return None
    return (current[0] - previous[0]) / (current[1] - previous[1]) * 100


def main() -> None:
    if sys.platform != "win32":
        return
    try:
        state = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    now = time.time()
    if now - state.get("checked", 0) < CHECK_EVERY_S:
        return
    current = cpu_times()
    free_mb, total_mb = memory_mb()
    state, text = decide(state, now, free_mb, total_mb, cpu_percent(state.get("cpu"), current))
    state["cpu"] = list(current)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(state), encoding="utf-8")
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": text}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
