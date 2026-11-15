"""Check: remind a self-drive chat to hand over when its context is over the limit.

Runs on ScheduleWakeup (every round end). The logic lives in `hooks/context_guard.py`, which
also still works as a standalone hook for chats that registered it before the dispatcher existed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import context_guard

EVENTS = {"PreToolUse"}
TOOLS = {"ScheduleWakeup"}


def run(payload):
    return context_guard.reminder(payload)
