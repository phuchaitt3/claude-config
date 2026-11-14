"""Stop hook: stop a self-paced /loop (self-drive) from ending silently when a turn forgets to reschedule.

Since Claude Code 2.1.319 a self-paced /loop ends as soon as a turn finishes without calling
`ScheduleWakeup` (changelog, 2026-11-06). The self-drive brief asks every round to end with that
call (step 7), but a text rule gets less reliable as a long turn's context grows (standard:
findings/agent-loop-control-enforcement, checked 2026-11-14). This hook enforces it at the point
of use: when a turn that belongs to a self-drive loop ends with no wakeup pending and no
background task running, it tells the chat to schedule the next round, or to stop on purpose.

How it knows a self-paced loop is live: the transcript holds a message that starts with the /loop
skill header (the loop's prompt is the model's own paraphrase of the brief, so the brief's wording
cannot be matched), and the last `ScheduleWakeup` call after it was not `stop: true`. A fixed
interval loop keeps its wakeups in `session_crons`, so it stays silent.
The Stop payload's `session_crons` (pending wakeups) and `background_tasks` (work that will wake
the chat) are both empty. One nudge per turn (`stop_hook_active`); Claude Code also caps
consecutive continuations at 8. Silent in an ordinary chat, after a deliberate stop, on any missing
field, and on any error: a broken hook must never trap a turn.

The same script also runs at SessionStart (since workflow 0.53.0): a pending `ScheduleWakeup` lives
in the session's process, so a resume in a new process (extension reload or update, `--resume`)
drops it while the transcript still shows a live loop (tested 2026-11-14, Claude Code 2.1.325).
When a session starts on a transcript whose loop is live, it tells the chat to re-arm. It cannot
wake an idle chat: the context reaches the model only when the next turn runs. Silent after
`compact`, where the process and its wakeups survive.

Known limit: after a user cancels a loop with Esc (no `stop: true` call), a later ordinary turn in
the same session gets one nudge per turn; the nudge text says to ignore it when the user stopped
the loop.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

NUDGE = (
    "Self-drive loop: this turn is ending with no wakeup pending and no background task running, "
    "which ends the loop (Claude Code 2.1.319 and later). Call ScheduleWakeup now with the same "
    "loop prompt (a delay of 60 seconds or more), or with stop: true if step 5 of the brief says "
    "to stop. If the user stopped the loop themselves, ignore this."
)

RESUME_NOTE = (
    "A self-drive loop was running in this session before it restarted. Pending wakeups do not "
    "survive a restart. Re-arm now: read the resume note in the morning summary and call "
    "ScheduleWakeup with the loop prompt, or stop: true if the user stopped the loop."
)


def _texts(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return "\n".join(parts)


def loop_live(entries: list[dict]) -> bool:
    """True when a self-paced loop was started and its last ScheduleWakeup was not `stop: true`."""
    started = False
    stopped = False
    for entry in entries:
        message = entry.get("message") or {}
        if entry.get("type") == "user":
            text = _texts(message.get("content"))
            if text.lstrip().startswith("# /loop"):
                started, stopped = True, False
        elif entry.get("type") == "assistant":
            for block in message.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use" \
                        and block.get("name") == "ScheduleWakeup":
                    stopped = bool((block.get("input") or {}).get("stop"))
    return started and not stopped


def read_entries(path: str) -> list[dict]:
    entries: list[dict] = []
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return entries
    for raw in lines:
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict):
            entries.append(entry)
    return entries


def should_nudge(payload: dict, entries: list[dict]) -> bool:
    if payload.get("stop_hook_active"):
        return False
    crons = payload.get("session_crons")
    tasks = payload.get("background_tasks")
    if not isinstance(crons, list) or not isinstance(tasks, list):
        return False  # registry not reachable: say nothing
    if crons or any(
        isinstance(t, dict) and str(t.get("status", "")).lower() in {"running", "pending"}
        for t in tasks
    ):
        return False
    return loop_live(entries)


def should_rearm(payload: dict, entries: list[dict]) -> bool:
    """SessionStart: a live loop in the transcript has lost its wakeup, except after compact."""
    if str(payload.get("source", "")).lower() == "compact":
        return False
    return loop_live(entries)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or not payload.get("transcript_path"):
            return 0
        entries = read_entries(str(payload["transcript_path"]))
        if payload.get("hook_event_name") == "SessionStart":
            event, text = "SessionStart", RESUME_NOTE
            if not should_rearm(payload, entries):
                return 0
        else:
            event, text = "Stop", NUDGE
            if not should_nudge(payload, entries):
                return 0
    except Exception:  # a guard against a slip: never trap the turn on a bug
        return 0
    json.dump(
        {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}},
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
