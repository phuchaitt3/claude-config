"""PreToolUse hook: refuse `gh pr create`, `gh pr comment` and `gh pr merge` until the chat has
loaded the `workflow:pr-review` skill.

Why: the working rules say to load that skill before opening, reviewing or merging a pull request,
but a rule in a long text is easy to miss, and a chat then asked the user whether it may load it
(2026-11-17). The hook reads the chat's own transcript (`transcript_path` in the payload) for a
`Skill` call naming `workflow:pr-review`, or a `/workflow:pr-review` command, and refuses with the
instruction to load it. After one load the transcript holds it, so later calls pass.

A guard against forgetting, not a security boundary: a command in a form it does not parse gets
past it. Fails open: no transcript path, an unreadable transcript or any error lets the command run
(standard: findings/agent-permission-enforcement, checked 2026-11-05).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_PR_COMMAND = re.compile(r"\bgh(?:\.exe)?\s+(?:-\S+\s+\S+\s+)*pr\s+(create|comment|merge)\b", re.I)
_LOADED = re.compile(
    r'"skill"\s*:\s*"workflow:pr-review"|<command-name>/?workflow:pr-review</command-name>'
)

REASON = (
    "Load the `workflow:pr-review` skill first (Skill tool, no need to ask the user): the working "
    "rules require it before opening, reviewing or merging a pull request. Then run this command "
    "again."
)


def needs_skill(command: str) -> bool:
    return _PR_COMMAND.search(command) is not None


def skill_loaded(transcript: Path) -> bool:
    return _LOADED.search(transcript.read_text(encoding="utf-8", errors="replace")) is not None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if payload.get("tool_name") not in ("Bash", "PowerShell"):
            return 0
        tool_input = payload.get("tool_input")
        command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
        path = payload.get("transcript_path")
        if not path or not needs_skill(command) or skill_loaded(Path(path)):
            return 0
    except Exception:  # fail open
        return 0
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": REASON,
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
