"""Check: tell a chat which laptop mode is on (user's decision, 2026-11-27, global scope).

The laptop has two modes, switched by the user's scripts: `scripts/game.ps1` (CPU turbo on, GPU clock
cap off, Lenovo Performance: gaming and normal use) and `scripts/night.ps1` (CPU max 99% so turbo off,
GPU capped at 1000-1350 MHz, Lenovo Quiet: long runs). It adds one line once per chat, at its first
prompt, and again before a Bash or PowerShell call tagged `# estimate:` over 10 minutes while the
laptop is not in night mode. Detail: `workflow:gpu-cap`, "Modes".
Why: a chat asked the user whether to keep "gaming mode" without knowing the two scripts existed,
and the user had to explain them again.

Silent on a machine with no battery (the PC has no modes) or off Windows. Lenovo mode is not read:
it needs Lenovo Legion Toolkit with administrator rights.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

EVENTS = {"UserPromptSubmit", "PreToolUse"}
LONG_RUN_MIN = 10.0
SEEN_DIR = Path.home() / ".claude" / "hook-cache" / "laptop-mode-seen"
CAP_MARKER = Path.home() / ".gpu-guard" / "clock-cap"
_ESTIMATE = re.compile(r"#\s*estimate:\s*(\d+(?:\.\d+)?)\s*(s|sec|m|min|h|hr)?(?![A-Za-z])", re.I)
_AC_INDEX = re.compile(r"Current AC Power Setting Index:\s*0x([0-9a-fA-F]+)")


def has_battery() -> bool:
    try:
        import ctypes

        class _Status(ctypes.Structure):
            _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte),
                        ("BatteryLifePercent", ctypes.c_byte), ("SystemStatusFlag", ctypes.c_byte),
                        ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]

        s = _Status()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s)):  # type: ignore[attr-defined]
            return False
        return (s.BatteryFlag & 0xFF) not in (128, 255)  # 128: no battery, 255: unknown
    except (AttributeError, OSError):
        return False


def _boot_time() -> float | None:
    try:
        import ctypes
        import time

        return time.time() - ctypes.windll.kernel32.GetTickCount64() / 1000  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        return None


def gpu_cap_on() -> bool:
    """Same test as `gpu_run.py cap status`: the marker exists and is newer than the boot."""
    try:
        set_at = CAP_MARKER.stat().st_mtime
    except OSError:
        return False
    boot = _boot_time()
    return boot is None or set_at >= boot


def cpu_max_pct() -> int | None:
    try:
        out = subprocess.run(["powercfg", "/query", "SCHEME_CURRENT", "SUB_PROCESSOR", "PROCTHROTTLEMAX"],
                             capture_output=True, text=True, timeout=5,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = _AC_INDEX.search(out or "")
    return int(m.group(1), 16) if m else None


def mode_line(cap_on: bool, cpu: int | None) -> tuple[str, str]:
    cpu_txt = "CPU ?" if cpu is None else f"CPU max {cpu}%"
    gpu_txt = "GPU cap ON (1350 MHz)" if cap_on else "GPU cap off"
    if cap_on and cpu is not None and cpu < 100:
        name = "NIGHT"
    elif not cap_on and cpu == 100:
        name = "GAME"
    else:
        name = "MIXED"
    return name, f"{name} ({cpu_txt}, {gpu_txt})"


def _minutes(command: str) -> float | None:
    found = _ESTIMATE.findall(command)
    if not found:
        return None
    value, unit = found[-1]
    n, unit = float(value), unit.lower()
    return n / 60 if unit in ("s", "sec") else n * 60 if unit in ("h", "hr") else n


def _first_prompt(session: str) -> bool:
    if not session:
        return False
    flag = SEEN_DIR / re.sub(r"[^A-Za-z0-9_-]", "_", session)
    if flag.exists():
        return False
    try:
        SEEN_DIR.mkdir(parents=True, exist_ok=True)
        flag.touch()
    except OSError:
        pass
    return True


def run(payload, *, battery=has_battery, cap=gpu_cap_on, cpu=cpu_max_pct, first=_first_prompt):
    event = payload.get("hook_event_name")
    if event == "PreToolUse":
        if payload.get("tool_name") not in ("Bash", "PowerShell"):
            return None
        minutes = _minutes(str((payload.get("tool_input") or {}).get("command", "")))
        if minutes is None or minutes <= LONG_RUN_MIN or not battery():
            return None
        name, line = mode_line(cap(), cpu())
        if name == "NIGHT":
            return None
        return (f"laptop-mode: {line}, and this run is estimated at {minutes:g} min. Long local runs use night "
                f"mode: ask the user before running `~/claude-config/scripts/night.ps1` in the daytime (an "
                f"overnight self-drive run sets it itself), and `game.ps1` puts game mode back "
                f"(`workflow:gpu-cap`, \"Modes\").")
    if event == "UserPromptSubmit":
        if not battery() or not first(str(payload.get("session_id", ""))):
            return None
        _, line = mode_line(cap(), cpu())
        return (f"laptop-mode: {line}. The user switches with `~/claude-config/scripts/game.ps1` (no caps, Lenovo "
                f"Performance: gaming, normal use) and `night.ps1` (CPU turbo off, GPU 1350 MHz, Lenovo Quiet: "
                f"long runs). \"Gaming mode\" means game.ps1. Before a long local run, load `workflow:gpu-cap`.")
    return None
