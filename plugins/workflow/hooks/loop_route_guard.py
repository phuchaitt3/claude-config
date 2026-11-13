"""PostToolUse hook (Edit|Write|NotebookEdit): keep a self-drive loop chat from doing the work itself.

Self-drive step 3 routes each task to a worker subagent, a `claude --bg` session, or (only for a
couple-of-tool-calls task) the loop chat. A text rule is dropped in a long loop (standard:
findings/agent-loop-control-enforcement, checked 2026-11-14); the first overnight run did every
task in the loop chat, so its context grew with every task. This hook counts the loop chat's own
file edits since its last delegation (an `Agent` call or a `claude --bg` command) and, from
`THRESHOLD` edits on, nudges once per `EVERY` further edits. It never blocks. Silent in an ordinary
chat (no live /loop), and on any error.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

THRESHOLD = 8
EVERY = 4
EDIT_TOOLS = {"Edit", "Write", "NotebookEdit"}

_spec = importlib.util.spec_from_file_location(
    "loop_guard", Path(__file__).with_name("loop_guard.py"))
loop_guard = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules.setdefault("loop_guard", loop_guard)
_spec.loader.exec_module(loop_guard)  # type: ignore[union-attr]


def _is_delegation(block: dict) -> bool:
    name = block.get("name")
    if name == "Agent":
        return True
    if name in {"Bash", "PowerShell"}:
        cmd = str((block.get("input") or {}).get("command", ""))
        return "--bg" in cmd and "claude" in cmd
    return False


def edits_since_delegation(entries: list[dict]) -> int:
    n = 0
    for entry in entries:
        if entry.get("type") != "assistant":
            continue
        for block in (entry.get("message") or {}).get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            if _is_delegation(block):
                n = 0
            elif block.get("name") in EDIT_TOOLS:
                n += 1
    return n


def nudge_text(n: int) -> str:
    return (
        f"Self-drive routing: this loop chat has made {n} file edits since it last delegated. "
        "Step 3 sends a code task to one worker subagent (Agent, isolation worktree, Sonnet) and "
        "a long run to `claude --bg`; the loop chat keeps only couple-of-tool-call tasks, so its "
        "context stays small. Write one line `Route: a/b/c because ...` and delegate the next "
        "task. If this edit is the tail of a task you already took, finish it, then delegate."
    )


def should_nudge(entries: list[dict]) -> int:
    if not loop_guard.loop_live(entries):
        return 0
    n = edits_since_delegation(entries)
    if n >= THRESHOLD and (n - THRESHOLD) % EVERY == 0:
        return n
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or not payload.get("transcript_path"):
            return 0
        n = should_nudge(loop_guard.read_entries(str(payload["transcript_path"])))
        if not n:
            return 0
    except Exception:
        return 0
    json.dump({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                       "additionalContext": nudge_text(n)}}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
