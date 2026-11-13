"""PreToolUse and PostToolUse hook (Edit|Write|NotebookEdit): keep a self-drive loop chat from doing the work itself.

Self-drive step 3 routes each task to a worker subagent, a `claude --bg` session, or (only for a
couple-of-tool-calls task) the loop chat. A text rule is dropped in a long loop (standard:
findings/agent-loop-control-enforcement, checked 2026-11-14); the first overnight run did every
task in the loop chat, so its context grew with every task. This hook counts the loop chat's own
file edits since its last delegation (an `Agent` call or a `claude --bg` command) and, from
`NUDGE_AT` edits on, nudges once per `EVERY` further edits (PostToolUse); at `BLOCK_AT` edits it
denies the next edit (PreToolUse, "pre" argument) until the chat delegates. Edits to handoff and
summary notes are exempt. Bash edits (sed, redirects) are not covered. Silent in an ordinary chat
(no live /loop), and on any error: a broken hook must never trap a turn.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

NUDGE_AT = 5
EVERY = 3
BLOCK_AT = 9
EXEMPT = ("handoff", "overnight-", "INBOX", "DONE.md")
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
    if n >= NUDGE_AT and (n - NUDGE_AT) % EVERY == 0:
        return n
    return 0


def should_block(entries: list[dict], file_path: str) -> int:
    if any(x in file_path for x in EXEMPT) or not loop_guard.loop_live(entries):
        return 0
    n = edits_since_delegation(entries)
    return n if n >= BLOCK_AT else 0


def deny_text(n: int) -> str:
    return (
        f"Self-drive routing: blocked. This loop chat has made {n} file edits without delegating. "
        "Hand the rest of this task to one worker subagent (Agent tool, isolation worktree, "
        "Sonnet, brief with the issue, files and the check to run, report of at most 10 lines), "
        "or a long run to `claude --bg`. The Agent call lifts this block. Notes in the handoff "
        "folder are exempt."
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or not payload.get("transcript_path"):
            return 0
        entries = loop_guard.read_entries(str(payload["transcript_path"]))
        if len(sys.argv) > 1 and sys.argv[1] == "pre":
            path = str((payload.get("tool_input") or {}).get("file_path", ""))
            n = should_block(entries, path)
            if not n:
                return 0
            json.dump({"hookSpecificOutput": {
                "hookEventName": "PreToolUse", "permissionDecision": "deny",
                "permissionDecisionReason": deny_text(n)}}, sys.stdout)
            return 0
        n = should_nudge(entries)
        if not n:
            return 0
    except Exception:
        return 0
    json.dump({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                       "additionalContext": nudge_text(n)}}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
