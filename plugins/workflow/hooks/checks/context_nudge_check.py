"""Check: tell a chat its context is large when the user sends a message (user's decision, 2026-11-27).

Runs on UserPromptSubmit, in every chat. Above 150000 tokens it asks the chat to suggest `/clear`,
and to ask first when the new message starts an unrelated task (working rules, "Context"). Why: the
chat cannot see its context size, and the text rule alone was missed (one daytime chat reached 269k
over unrelated tasks with no suggestion). Reminder only: it never resets, hands off or blocks.

The threshold is separate from self-drive's (`context_guard.THRESHOLD`, under its own trial), so
changing that trial does not change daytime chats. No source gives a figure; 150000 is a noise level
chosen from local transcripts (findings/agent-session-handoff-reset).

Right after `/compact` the last recorded usage is the size before compaction, so it stays silent
until the next model reply.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import context_guard

EVENTS = {"UserPromptSubmit"}
THRESHOLD = 150000
_COMPACTION = ('"compact_boundary"', '"isCompactSummary":true')


def _compacted_since_last_reply(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - context_guard.TAIL_BYTES))
            lines = f.read().decode("utf-8", errors="replace").splitlines()
    except OSError:
        return False
    for line in reversed(lines):
        if any(mark in line for mark in _COMPACTION):
            return True
        if '"usage"' in line and '"type":"assistant"' in line:
            return False
    return False


def run(payload):
    path = payload.get("transcript_path")
    if not path:
        return None
    ctx = context_guard.last_context(str(path))
    if ctx is None or ctx <= THRESHOLD or _compacted_since_last_reply(str(path)):
        return None
    return (f"context_nudge_check: this chat is at {round(ctx / 1000)}k tokens, and every call re-reads all "
            "of it. If this message starts a task unrelated to the earlier work, do not start it yet: give the "
            "size and say \"/clear and send this again, or say go to do it here\" (add a resume prompt if the "
            "task needs anything from this chat). If it continues the same work, do it, and at the next task "
            "boundary suggest /clear with a resume prompt. If the user already chose to stay, do not ask again "
            "until 50k more. Ignore this if the message is not from the user, or in an overnight loop or "
            "background worker.")
