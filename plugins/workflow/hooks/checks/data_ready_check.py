"""Check: tell the chat once a day when an issue that waits for data has enough of it.

Four claude-config issues stay open on purpose until local data exists (user's yes, 2026-11-19).
Each entry in `conditions` reads a local log; when its condition holds, the first message of a
chat that day gets one line, "claude-config #N has enough data now: <why>". Reminder only: it
never blocks. When an issue is closed, delete its entry here (and this file when none is left).

- #5  main_checkout and worktree_sweep skipped after /clear: needs a few logged `source=clear` starts.
- #15 context_report.py fix-up count: needs two weeks of 150K-threshold trial data (a date).
- #24 thermal watchdog durations: needs the first real `thermal_stopped` event.
- #21 keep_awake hold misses: act when the miss rate passes 5% of holds.
"""

import re
from datetime import date
from pathlib import Path

EVENTS = {"UserPromptSubmit"}
HOME = Path.home()
CACHE = HOME / ".claude" / "hook-cache"
GPU_GUARD = HOME / ".gpu-guard"
CLEAR_STARTS_NEEDED = 3
TRIAL_READY = date(2026, 11, 27)
MISS_RATE = 0.05
MIN_HOLDS = 50


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def clear_starts(cache: Path) -> str | None:
    n = len(re.findall(r"source=clear\b", _read(cache / "sessionstart.log")))
    if n >= CLEAR_STARTS_NEEDED:
        return f"{n} /clear starts are logged in sessionstart.log; compare them with the hook stamps"
    return None


def trial_date(today: date) -> str | None:
    if today >= TRIAL_READY:
        return "two weeks of 150K-threshold trial data should exist; run context_report.py --prs"
    return None


def thermal_alert(gpu: Path) -> str | None:
    if '"thermal_stopped"' in _read(gpu / "events.jsonl"):
        return "a thermal_stopped event is logged; review the 5 and 2 minute durations against it"
    return None


def hold_misses(cache: Path) -> str | None:
    log = _read(cache / "keep_awake" / "holder.log")
    holds = log.count("holding for")
    misses = len(re.findall(r"no .* shell found", log))
    if holds >= MIN_HOLDS and misses / holds > MISS_RATE:
        return f"keep_awake missed {misses} of {holds} holds ({misses / holds:.1%}), over {MISS_RATE:.0%}"
    return None


def conditions(today: date, cache: Path, gpu: Path):
    return {
        5: lambda: clear_starts(cache),
        15: lambda: trial_date(today),
        24: lambda: thermal_alert(gpu),
        21: lambda: hold_misses(cache),
    }


def run(payload, today: date | None = None, cache: Path = CACHE, gpu: Path = GPU_GUARD):
    today = today or date.today()
    lines = []
    for number, check in conditions(today, cache, gpu).items():
        marker = cache / f"data-ready-{number}.date"
        if _read(marker).strip() == today.isoformat():
            continue
        try:
            why = check()
        except Exception:
            why = None
        if not why:
            continue
        try:
            cache.mkdir(parents=True, exist_ok=True)
            marker.write_text(today.isoformat(), encoding="utf-8")
        except OSError:
            pass
        lines.append(f"claude-config #{number} has enough data now: {why}. See the issue.")
    return "\n".join(lines) or None
