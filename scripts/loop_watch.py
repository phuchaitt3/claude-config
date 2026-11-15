"""Read-only watchdog helper: find the live self-paced /loop chat of each project folder.

A watchdog that checks fixed chat IDs goes wrong when the loop chat is replaced. This script
finds the chat when the check runs: for each project folder it lists
~/.claude/projects/<slug>/*.jsonl newest first and keeps transcripts with a live self-paced
/loop (same test as plugins/workflow/hooks/loop_guard.py: a ScheduleWakeup call, or a message
starting with "# /loop", and the last ScheduleWakeup not `stop: true`). One line per folder:

  <folder>: <session id> <agent name> last <local time> wakeup <delay>s set <local time>
      summary <path> <VERDICT>

`summary <path>` (just before the verdict) is the morning-summary file (`overnight-*.md`) the loop last
wrote to, read from its own transcript (a Write or Edit of it, or a shell command that redirects
into it), so a watchdog never guesses between `overnight-<date>.md` and a later run's
`overnight-<date>b.md`; `summary ?` when the transcript has none yet.

Verdicts: WAITING (a wakeup is pending: the last ScheduleWakeup came after the last real user
message, so the loop has not woken since), STALLED (no wakeup pending and the last turn is over
30 minutes old), RUNNING (no wakeup pending, last turn recent), NO LOOP (none live).
Transcripts untouched for more than --max-age-hours (default 24) are ignored, so a dead chat
from an earlier day is not reported as the loop.

Usage: python loop_watch.py <folder> [<folder> ...] [--projects-dir DIR] [--now ISO]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

STALL_SECONDS = 30 * 60
LOOP_HEADER = "# /loop"  # as in plugins/workflow/hooks/loop_guard.py


def slug(folder: str) -> str:
    """Claude Code's project directory name: every non-alphanumeric character becomes '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", folder)


def read_entries(path: Path) -> list[dict]:
    out: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    for raw in lines:
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict):
            out.append(entry)
    return out


def _texts(content) -> str:
    if isinstance(content, str):
        return content
    return "\n".join(
        str(b.get("text", "")) for b in content or []
        if isinstance(b, dict) and b.get("type") == "text"
    )


SUMMARY_RE = re.compile(r"""[^\s'"<>|;&]*overnight-[\w-]+\.md""")


def summary_writes(block: dict) -> list[str]:
    """Paths of overnight-*.md files this tool call writes to."""
    inp = block.get("input") or {}
    if block.get("name") in ("Write", "Edit"):
        path = str(inp.get("file_path", ""))
        return [path] if SUMMARY_RE.fullmatch(path.split("/")[-1].split("\\")[-1]) else []
    cmd = str(inp.get("command", ""))
    # a redirect (> or >>, or tee) into the file; a plain read (cat, tail) does not count
    return [m.group(1) for m in re.finditer(
        r"""(?:>>?|\btee(?:\s+-a)?)\s*["']?([^\s'"<>|;&]*overnight-[\w-]+\.md)""", cmd)]


def _is_tool_result(content) -> bool:
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content
    )


def _ts(value) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def analyse(entries: list[dict]) -> dict | None:
    """Return the loop's state, or None when no self-paced loop is live."""
    started = stopped = False
    session = name = None
    last_activity = None
    wake = None  # (delay seconds, set at)
    wake_pending = False
    summary = None
    for e in entries:
        session = e.get("sessionId") or session
        if e.get("type") == "agent-name" and e.get("agentName"):
            name = e["agentName"]
        kind = e.get("type")
        if kind not in ("user", "assistant"):
            continue
        when = _ts(e.get("timestamp"))
        if when:
            last_activity = when
        content = (e.get("message") or {}).get("content")
        if kind == "user":
            if _is_tool_result(content):
                continue
            text = _texts(content).lstrip()
            if text.startswith(LOOP_HEADER):
                started, stopped, wake, wake_pending = True, False, None, False
            elif not e.get("origin") and not text.startswith("<"):
                # a fired wakeup arrives as plain text with no origin. A human, a peer chat or a
                # task notification carries an origin; system reminders, local slash commands
                # and hook notices start with "<": none of these is a wakeup, so a pending
                # wakeup stays pending
                wake_pending = False
        else:
            for b in content or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    for path in summary_writes(b):
                        summary = path
                if isinstance(b, dict) and b.get("type") == "tool_use" \
                        and b.get("name") == "ScheduleWakeup":
                    inp = b.get("input") or {}
                    started = True  # a ScheduleWakeup call marks a self-paced loop
                    stopped = bool(inp.get("stop"))
                    if stopped:
                        wake_pending = False
                    else:
                        wake = (inp.get("delaySeconds"), when)
                        wake_pending = True
    if not (started and not stopped):
        return None
    return {"session": session, "name": name, "last": last_activity,
            "wake": wake, "pending": wake_pending, "summary": summary}


def find_loop(folder: str, projects_dir: Path, now: float, max_age_h: float) -> dict | None:
    want = slug(folder).lower()
    files: list[Path] = []
    if projects_dir.is_dir():
        for d in projects_dir.iterdir():
            if d.is_dir() and d.name.lower() == want:
                files += list(d.glob("*.jsonl"))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for f in files:
        if now - f.stat().st_mtime > max_age_h * 3600:
            break  # sorted newest first: the rest are older
        state = analyse(read_entries(f))
        if state:
            return state
    return None


def local(t: datetime | None) -> str:
    return t.astimezone().strftime("%Y-%m-%d %H:%M") if t else "?"


def summary_path(folder: str, path: str | None) -> str:
    """The summary file as an absolute path when it is relative to the checkout."""
    if not path:
        return "?"
    p = Path(path)
    if not p.is_absolute() and not path.startswith(("~", "/")):
        p = Path(folder) / p
    return str(p)


def line(folder: str, state: dict | None, now: datetime) -> str:
    if state is None:
        return f"{folder}: NO LOOP"
    if state["wake"]:
        delay, set_at = state["wake"]
        wake = f"wakeup {delay}s set {local(set_at)}"
    else:
        wake = "wakeup none"
    if state["pending"]:
        verdict = "WAITING"
    elif state["last"] and (now - state["last"]).total_seconds() > STALL_SECONDS:
        verdict = "STALLED"
    else:
        verdict = "RUNNING"
    return (f"{folder}: {state['session']} {state['name'] or '(no name)'} "
            f"last {local(state['last'])} {wake} "
            f"summary {summary_path(folder, state.get('summary'))} {verdict}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folders", nargs="+")
    ap.add_argument("--projects-dir", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--max-age-hours", type=float, default=24)
    ap.add_argument("--now", help="ISO time for tests (default: the clock)")
    args = ap.parse_args(argv)
    now_dt = _ts(args.now) if args.now else datetime.now(timezone.utc)
    now = now_dt.timestamp() if args.now else time.time()
    for folder in args.folders:
        state = find_loop(folder, Path(args.projects_dir), now, args.max_age_hours)
        print(line(folder, state, now_dt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
