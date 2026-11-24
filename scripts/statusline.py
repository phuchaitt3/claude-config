"""Claude Code status line: model name, how full the context window is, and the 5-hour quota.

Claude Code pipes a JSON object to stdin on each update; `context_window.used_percentage` is the
share of the window in use. The percentage is coloured green under 50, yellow from 50 to 79 and red
from 80, so the user can see when to run /compact or /clear (working rules, "Context"). Prints
nothing if the input is missing or malformed: a status line must never get in the way.

It also shows the 5-hour usage limit (`rate_limits.five_hour.used_percentage`) and writes the
`rate_limits` block to `~/.claude/hook-cache/quota.json`, because no hook input carries it; the
`quota_watch` hook reads that file so a self-drive loop can pause before the limit
(standard: findings/claude-code-usage-limit-resume, checked 2026-11-14).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

GREEN, YELLOW, RED, RESET = "\033[32m", "\033[33m", "\033[31m", "\033[0m"
QUOTA_FILE = Path.home() / ".claude" / "hook-cache" / "quota.json"


def colour(percent: float) -> str:
    if percent >= 80:
        return RED
    if percent >= 50:
        return YELLOW
    return GREEN


def render(data: dict) -> str:
    model = (data.get("model") or {}).get("display_name") or ""
    percent = (data.get("context_window") or {}).get("used_percentage")
    parts = [model] if model else []
    if isinstance(percent, (int, float)):
        parts.append(f"{colour(percent)}ctx {percent:.0f}%{RESET}")
    five = ((data.get("rate_limits") or {}).get("five_hour") or {}).get("used_percentage")
    if isinstance(five, (int, float)):
        parts.append(f"{colour(five)}5h {five:.0f}%{RESET}")
    return " | ".join(parts)


def read_saved(path: Path) -> dict:
    try:
        return (json.loads(path.read_text(encoding="utf-8")).get("rate_limits") or {})
    except (OSError, ValueError, AttributeError):
        return {}


def is_stale(limits: dict, saved: dict, now: float) -> bool:
    """True for a snapshot an idle chat is still sending from before the last quota reset.

    Each chat's status line passes the quota as of its own last reply, so a chat that has been idle
    sends old numbers, and they were written over the shared file and logged (2026-11-24: weekly 19%
    shown while 24% was true). A block whose reset time has passed belongs to an old window; and within
    one window the used percentage never falls, so a lower number than the saved one for the same reset
    time is older than the saved one. A new reset time is accepted: a fresh window starts low.
    """
    for key in ("five_hour", "seven_day"):
        block = limits.get(key)
        if not isinstance(block, dict):
            continue
        try:
            resets, used = float(block["resets_at"]), float(block["used_percentage"])
        except (KeyError, TypeError, ValueError):
            continue
        if resets <= now:
            return True
        old = saved.get(key) if isinstance(saved.get(key), dict) else None
        try:
            if old and float(old["resets_at"]) == resets and float(old["used_percentage"]) > used:
                return True
        except (KeyError, TypeError, ValueError):
            pass
    return False


def save_quota(data: dict, path: Path = QUOTA_FILE, now: float | None = None) -> bool:
    """Write the rate_limits block with a timestamp; True if written. Never raises."""
    limits = data.get("rate_limits")
    if not isinstance(limits, dict) or not limits:
        return False
    now_s = time.time() if now is None else now
    if is_stale(limits, read_saved(path), now_s):
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        record = {"written_at": time.time() if now is None else now, "rate_limits": limits}
        tmp.write_text(json.dumps(record), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        return False
    return True


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            return 0
        line = render(data)
        save_quota(data)
    except (ValueError, OSError):
        return 0
    if line:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
