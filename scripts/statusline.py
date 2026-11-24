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
QUOTA_LOG = Path.home() / ".claude" / "quota-log.jsonl"
LOG_EVERY = 30 * 60


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


MAX_AGE = 600  # seconds since the chat's last model reply; older snapshots are not trusted


def reply_age(transcript: str | None, now: float) -> float | None:
    """Seconds since the last model reply in the chat's transcript, or None when it cannot be told.

    The quota a chat's status line gets is as of that reply, so this is the most the snapshot can lag.
    A snapshot a chat sends after sitting idle for an hour is an hour old, and if nobody else wrote a
    higher number in between it cannot be told from a fresh one by its value alone.
    """
    from datetime import datetime
    try:
        with open(transcript, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 262144))
            tail = f.read().decode("utf-8", errors="ignore").splitlines()
        for line in reversed(tail):
            if '"usage"' in line:
                ts = json.loads(line)["timestamp"]
                return now - datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (OSError, TypeError, ValueError, KeyError):
        pass
    return None


def is_stale(limits: dict, saved: dict, now: float, age: float | None = None) -> bool:
    """True for a snapshot an idle chat is still sending from before the last quota reset.

    Each chat's status line passes the quota as of its own last reply, so a chat that has been idle
    sends old numbers, and they were written over the shared file and logged (2026-11-24: weekly 19%
    shown while 24% was true). A block whose reset time has passed belongs to an old window; and within
    one window the used percentage never falls, so a lower number than the saved one for the same reset
    time is older than the saved one. A new reset time is accepted: a fresh window starts low.
    A snapshot older than MAX_AGE (`age`, from `reply_age`) is stale whatever its value, which catches
    the one a value check cannot: an idle chat's old number that is not lower than the saved one.
    """
    if age is not None and age > MAX_AGE:
        return True
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


def log_quota(limits: dict, session_id: str, age: float | None, log: Path, now: float) -> bool:
    """Append one line (time, chat, age, 5-hour and weekly percentages and resets) to the quota log.

    Logged here, on each status-line render after a reply, instead of at the next prompt: the snapshot is
    then seconds old and the chat that sent it is the one named, so a loop that sleeps for an hour still
    leaves a fresh row and `selfdrive_cost.clean` has an `age` to check. A line is added when a
    percentage changed or after LOG_EVERY seconds. Never raises.
    """
    try:
        row = {"t": round(now), "session": session_id, "age": None if age is None else round(age)}
        for key, name in (("five_hour", "five"), ("seven_day", "week")):
            if isinstance(limits.get(key), dict):
                row[name] = float(limits[key]["used_percentage"])
                row[name + "_resets"] = float(limits[key]["resets_at"])
        if "week" not in row and "five" not in row:
            return False
        last = None
        if log.exists():
            with log.open("rb") as handle:
                lines = handle.read().splitlines()
            last = json.loads(lines[-1]) if lines else None
        if last and last.get("five") == row.get("five") and last.get("week") == row.get("week") \
                and now - float(last["t"]) < LOG_EVERY:
            return False
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        return False
    return True


def save_quota(data: dict, path: Path = QUOTA_FILE, now: float | None = None, age: float | None = None,
               log: Path | None = QUOTA_LOG) -> bool:
    """Write the rate_limits block with a timestamp and log it; True if written. Never raises."""
    limits = data.get("rate_limits")
    if not isinstance(limits, dict) or not limits:
        return False
    now_s = time.time() if now is None else now
    if is_stale(limits, read_saved(path), now_s, age):
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        record = {"written_at": now_s, "rate_limits": limits, "age": age}
        tmp.write_text(json.dumps(record), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        return False
    if log is not None:
        log_quota(limits, str(data.get("session_id") or ""), age, log, now_s)
    return True


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            return 0
        line = render(data)
        save_quota(data, age=reply_age(data.get("transcript_path"), time.time()))
    except (ValueError, OSError):
        return 0
    if line:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
