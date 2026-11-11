"""Run-time estimates against actual run times (claude-config, user's decision 2026-11-11).

A command expected to take over 10 minutes carries a marker, `# estimate: 20m` (also `90s`, `2h`;
a bare number means minutes). This file does three things, each failing open:

- PreToolUse (Bash|PowerShell), no argument: for a foreground command, remembers the start time;
  for any command with a marker, adds the past actual/estimate ratio to the chat's context, so the
  estimate can be scaled before an approval threshold is applied.
- `post` (PostToolUse): for a foreground command, appends one line to the log with the actual time
  when it had a marker, or took over UNTAGGED_MIN minutes without one.
- `record(...)`: called by keep_awake's holder when a background command exits (the only place that
  sees when a background command ends), for every held command, tagged or not.

The log is `~/.claude/run-estimates.jsonl`, local only: command lines hold private paths, and the
config repo is public. Fields: ts, tool, background, estimate_min (null when untagged), actual_min,
command (first 100 characters).
"""

from __future__ import annotations

import json
import re
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

LOG = Path.home() / ".claude" / "run-estimates.jsonl"
PENDING_DIR = Path.home() / ".claude" / "hook-cache" / "run_estimate"
UNTAGGED_MIN = 10.0  # a foreground command with no marker is logged only above this
MIN_RUNS = 3  # tagged runs needed before a ratio is shown
RECENT = 20  # tagged runs the ratio is computed from
_MARKER = re.compile(r"#\s*estimate:\s*(\d+(?:\.\d+)?)\s*(s|sec|m|min|h|hr)?(?![A-Za-z])", re.IGNORECASE)


def parse_estimate(command: str) -> float | None:
    """The last `# estimate:` marker in the command, in minutes, or None."""
    found = _MARKER.findall(command)
    if not found:
        return None
    value, unit = found[-1]
    minutes = float(value)
    unit = unit.lower()
    if unit.startswith("s"):
        return minutes / 60
    if unit.startswith("h"):
        return minutes * 60
    return minutes


def ratio(entries: list[dict]) -> tuple[float, int] | None:
    """Median actual/estimate over the most recent tagged runs, and how many, or None."""
    ratios = [
        e["actual_min"] / e["estimate_min"]
        for e in entries
        if e.get("estimate_min") and e.get("actual_min") is not None
    ][-RECENT:]
    if len(ratios) < MIN_RUNS:
        return None
    return statistics.median(ratios), len(ratios)


def read_log(path: Path | None = None) -> list[dict]:
    path = path or LOG
    out = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def record(tool: str, background: bool, command: str, actual_s: float, path: Path | None = None) -> None:
    """Append one run to the log."""
    path = path or LOG
    entry = {
        "ts": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": tool,
        "background": background,
        "estimate_min": parse_estimate(command),
        "actual_min": round(actual_s / 60, 2),
        "command": " ".join(command.split())[:100],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def pending_path(payload: dict) -> Path:
    key = re.sub(r"[^\w-]", "", str(payload.get("tool_use_id") or "")) or "none"
    return PENDING_DIR / f"{key}.json"


def advice(estimate: float, entries: list[dict]) -> str:
    """The context line for a tagged command, or "" until there are enough past runs."""
    found = ratio(entries)
    if found is None:
        return ""
    r, n = found
    return (
        f"run-estimate: your estimate is {estimate:g} min; over your last {n} tagged runs the "
        f"actual time was {r:.2f}x the estimate (median), so expect about {estimate * r:.0f} min. "
        "Apply any approval threshold to that figure."
    )


def pre(payload: dict) -> None:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return
    command = str(tool_input.get("command", ""))
    if not tool_input.get("run_in_background"):
        PENDING_DIR.mkdir(parents=True, exist_ok=True)
        pending_path(payload).write_text(json.dumps({"start": time.time()}), encoding="utf-8")
    estimate = parse_estimate(command)
    line = advice(estimate, read_log()) if estimate is not None else ""
    if line:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "additionalContext": line,
        }}))


def post(payload: dict) -> None:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict) or tool_input.get("run_in_background"):
        return
    path = pending_path(payload)
    try:
        start = float(json.loads(path.read_text(encoding="utf-8"))["start"])
    except (OSError, ValueError, KeyError):
        return
    path.unlink(missing_ok=True)
    command = str(tool_input.get("command", ""))
    actual = time.time() - start
    if parse_estimate(command) is not None or actual >= UNTAGGED_MIN * 60:
        record(str(payload.get("tool_name")), False, command, actual)


def main(argv: list[str]) -> int:
    try:
        payload = json.load(sys.stdin)
        if isinstance(payload, dict) and payload.get("tool_name") in ("Bash", "PowerShell"):
            (post if argv[:1] == ["post"] else pre)(payload)
    except Exception:  # noqa: BLE001, S110  never get in the way of a tool call
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
