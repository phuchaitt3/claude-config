"""Check: tell a chat which machine it runs on (user's decision, 2026-11-28, global scope).

One line once per chat, at its first prompt. A battery means the laptop, none means the PC (the test
`setup-machine.ps1` and self-drive use). Silent when that cannot be read. Why: a chat on the PC took
the user's word "laptop" and reported the PC's processes, memory and session IDs as the laptop's.
Nothing in a chat's start-up context names the machine.
"""

from __future__ import annotations

import platform
import re
import sys
from pathlib import Path

EVENTS = {"UserPromptSubmit"}
SEEN_DIR = Path.home() / ".claude" / "hook-cache" / "machine-seen"
NO_BATTERY = 128
UNKNOWN = 255


def battery_flag() -> int | None:
    """Windows' battery flag, or None where it cannot be read."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes

        status = (ctypes.c_byte * 12)()  # SYSTEM_POWER_STATUS; the second byte is BatteryFlag
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):  # type: ignore[attr-defined]
            return None
        return status[1] & 0xFF
    except (AttributeError, OSError):
        return None


def line(flag: int | None, host: str) -> str | None:
    if flag is None or flag == UNKNOWN:
        return None
    pc = bool(flag & NO_BATTERY)
    here, other = ("PC", "laptop") if pc else ("laptop", "PC")
    battery = "no battery" if pc else "has a battery"
    return (f"machine: this chat runs on the {here} ({host}, {battery}). Commands, files, processes and "
            f"readings here are the {here}'s, not the {other}'s.")


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


def run(payload, *, battery=battery_flag, host=platform.node, first=_first_prompt):
    if payload.get("hook_event_name") != "UserPromptSubmit":
        return None
    text = line(battery(), host())
    if text is None or not first(str(payload.get("session_id", ""))):
        return None
    return text
