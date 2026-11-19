"""PreToolUse hook (EnterWorktree|ExitWorktree): refuse both tools in an overnight self-drive session.

Both tools ask a permission prompt that nobody answers overnight, so the chat stalls (a book-rag-app
run stalled on three of them, 2026-11-18, even though the self-drive skill said not to call them;
a text rule is dropped in a long run, standard: findings/agent-loop-control-enforcement, checked
2026-11-14). A PreToolUse deny is decided before the permission prompt, so the call never reaches
the user. An overnight session is one started with CLAUDE_CODE_LOOP_KEEPALIVE=1 (selfdrive.ps1 and
START-OVERNIGHT.md set it; the variable is inherited by the hook), or one whose transcript shows a
live self-paced loop. Silent in an ordinary chat, and on any error: a broken hook must never trap
a turn.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

REASON = (
    "Overnight self-drive session: EnterWorktree and ExitWorktree are refused here, because they "
    "ask a permission prompt nobody answers overnight. Use `git worktree add ../<ID>-<slug>` "
    "from the main checkout and work in it with absolute paths."
)

_spec = importlib.util.spec_from_file_location(
    "loop_guard", Path(__file__).with_name("loop_guard.py"))
loop_guard = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules.setdefault("loop_guard", loop_guard)
_spec.loader.exec_module(loop_guard)  # type: ignore[union-attr]


def overnight(env: dict, transcript_path: str | None) -> bool:
    if env.get("CLAUDE_CODE_LOOP_KEEPALIVE") == "1":
        return True
    if transcript_path:
        return bool(loop_guard.loop_live(loop_guard.read_entries(transcript_path)))
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return 0
        if payload.get("tool_name") not in {"EnterWorktree", "ExitWorktree"}:
            return 0
        if not overnight(dict(os.environ), payload.get("transcript_path")):
            return 0
    except Exception:
        return 0
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": REASON}}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
