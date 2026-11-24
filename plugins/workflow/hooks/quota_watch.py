"""UserPromptSubmit hook: tell a chat when the 5-hour usage limit is nearly used up.

No hook input carries the subscription quota; the status line does (`rate_limits.five_hour`), and
`scripts/statusline.py` writes it to `~/.claude/hook-cache/quota.json`. This hook reads that file
on every prompt, including each `/loop` wakeup and each background worker's report, and at or above
the threshold adds one line: the percentage, the reset time, and the pause the `workflow:self-drive`
skill asks for ("Quota pause"). Below the threshold, or when the file is missing or older than
`STALE_SECONDS`, it says nothing.

Why pause before the limit: a turn that hits the limit and then more turns firing into it (a loop
wakeup, a worker report) stop Claude Code's built-in auto-continue ("the continued task kept hitting
the limit"), so the run stalls until someone types; pausing on the known reset time is the usual
rate-limit practice (standard: findings/claude-code-usage-limit-resume, checked 2026-11-14).

It also appends the 5-hour and weekly percentages to `~/.claude/quota-log.jsonl` (`log_sample`), so
`selfdrive_cost.py` can say how much of the weekly quota a run used (user's decision, 2026-11-20).
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

QUOTA_FILE = Path.home() / ".claude" / "hook-cache" / "quota.json"
QUOTA_LOG = Path.home() / ".claude" / "quota-log.jsonl"
LOG_EVERY = 30 * 60
THRESHOLD = 90.0
STALE_SECONDS = 30 * 60
RESUME_MARGIN = 120
MAX_WAKEUP = 3600


def read_quota(path: Path = QUOTA_FILE, now: float | None = None) -> tuple[float, float] | None:
    """(5-hour used percentage, reset epoch seconds), or None when missing, broken or stale."""
    now = time.time() if now is None else now
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        written = float(record["written_at"])
        five = record["rate_limits"]["five_hour"]
        used, resets = float(five["used_percentage"]), float(five["resets_at"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if now - written > STALE_SECONDS or resets <= now:
        return None
    return used, resets


def log_sample(
    session_id: str, path: Path = QUOTA_FILE, log: Path = QUOTA_LOG, now: float | None = None
) -> bool:
    """Append one line (time, session, 5-hour and weekly percentages and resets) to the quota log.

    A line is added when a percentage changed since the last line, or after LOG_EVERY seconds, so the
    log stays small and still shows when each step happened. Returns True if a line was written.
    Never raises: the log must not get in the way of a prompt.
    """
    now = time.time() if now is None else now
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        if now - float(record["written_at"]) > STALE_SECONDS:
            return False
        limits = record["rate_limits"]
        row = {"t": round(now), "session": session_id}
        for key, name in (("five_hour", "five"), ("seven_day", "week")):
            if key in limits:
                row[name] = float(limits[key]["used_percentage"])
                row[name + "_resets"] = float(limits[key]["resets_at"])
        if "week" not in row and "five" not in row:
            return False
        if any(row.get(k + "_resets", now + 1) <= now for k in ("five", "week")):
            return False  # a snapshot from before the last reset (statusline.is_stale)
        last = None
        if log.exists():
            with log.open("rb") as handle:
                lines = handle.read().splitlines()
            last = json.loads(lines[-1]) if lines else None
        if (
            last
            and last.get("five") == row.get("five")
            and last.get("week") == row.get("week")
            and now - float(last["t"]) < LOG_EVERY
        ):
            return False
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        return False
    return True


def message(used: float, resets: float, now: float, threshold: float = THRESHOLD) -> str:
    """The line to add, or '' below the threshold."""
    if used < threshold:
        return ""
    wait = int(resets - now) + RESUME_MARGIN
    clock = datetime.fromtimestamp(resets).strftime("%H:%M")
    return (
        f"Quota: 5-hour usage {used:.0f}% (threshold {threshold:.0f}%), resets at {clock} local, "
        f"in {wait // 60} min. In a self-drive loop, follow `workflow:self-drive` \"Quota pause\": start "
        f"no new worker or long step; start `sleep {wait}` as a background command (keeps the machine "
        f"awake and wakes you after the reset); end the round with ScheduleWakeup "
        f"delaySeconds={min(wait, MAX_WAKEUP)} and do nothing but check the quota until it has reset. "
        "Outside a loop, finish the current step and tell the user."
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    if payload.get("hook_event_name") != "UserPromptSubmit":
        return
    now = time.time()
    log_sample(str(payload.get("session_id") or ""), now=now)
    quota = read_quota(now=now)
    if quota is None:
        return
    try:
        text = message(quota[0], quota[1], now)
    except (OverflowError, OSError, ValueError):  # an absurd reset time: say nothing
        return
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": text}}))


if __name__ == "__main__":
    main()
