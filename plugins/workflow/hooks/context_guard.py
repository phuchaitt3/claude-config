"""PreToolUse hook on ScheduleWakeup: run the self-drive context check at every round end.

Self-drive step 7a asks a chat to measure its context at the end of a round and hand over to a
successor above 150K. As a text rule it was missed: on 2026-11-15 a round that ended with a merge
(not one of the round ends the rule listed) skipped the check, and the chat ran on to 170K with
three checks in about 90 calls. Every round ends with a `ScheduleWakeup` call (step 7), so this
hook reads the chat's context size there and, above the threshold, reminds the chat to hand over.

It reads only the tail of the transcript (the last model call's usage), writes nothing and logs
nothing; the trial log stays `context_size.py --log`, which the reminder tells the chat to run.
It never blocks: a `stop: true` call, a size at or under the threshold, a missing field, and any
error all stay silent, because a broken guard must never trap a turn. Daytime loops get the same
reminder; its text says to ignore it outside an overnight run (step 7a is overnight only).
"""

from __future__ import annotations

import json
import sys

# Keep equal to DEFAULT_THRESHOLD in skills/self-drive/context_size.py (a test checks this).
THRESHOLD = 150000
TAIL_BYTES = 400_000

REMINDER = (
    "Self-drive context check: this chat's context is {ctx} tokens, over the {limit} limit. "
    "Overnight run: follow step 7a before this wakeup. Run context_size.py --log, write the resume "
    "note to the morning-summary file, start the successor with claude --bg, confirm it in "
    "claude agents --json, then end this chat with ScheduleWakeup stop: true. A worker still "
    "running does not delay the handover for long: start no new task, worker or background session, "
    "finish what is in flight, and hand over at the latest 60 minutes after the first reading over "
    "the limit (record its time in the summary file), naming any unfinished task in the note. "
    "Not an overnight run (a daytime loop with the user present): ignore this."
)


def last_context(path: str) -> int | None:
    """Context size (input + cache read + cache creation) of the last main-thread model call."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - TAIL_BYTES))
            raw = f.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    for line in reversed(raw.splitlines()):
        if '"usage"' not in line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue  # the first line of the tail may be cut
        if not isinstance(entry, dict) or entry.get("type") != "assistant" or entry.get("isSidechain"):
            continue
        usage = (entry.get("message") or {}).get("usage")
        if not isinstance(usage, dict):
            continue
        return sum(int(usage.get(k) or 0) for k in (
            "input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    return None


def reminder(payload: dict, threshold: int = THRESHOLD) -> str | None:
    if payload.get("tool_name") != "ScheduleWakeup":
        return None
    if (payload.get("tool_input") or {}).get("stop"):
        return None
    path = payload.get("transcript_path")
    if not path:
        return None
    ctx = last_context(str(path))
    if ctx is None or ctx <= threshold:
        return None
    return REMINDER.format(ctx=ctx, limit=threshold)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        text = reminder(payload) if isinstance(payload, dict) else None
    except Exception:  # a guard against a slip: never trap the turn on a bug
        return 0
    if text:
        json.dump(
            {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": text}},
            sys.stdout,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
