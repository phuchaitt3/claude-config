"""PreToolUse hook: refuse a hand-typed `kaggle kernels push`.

A push of a kernel that already has a queued or running version leaves that version running and can
hold a second of the account's 2 shared GPU sessions with a run that is only waiting.
`scripts/kaggle_slots.py push` checks first (user's decision, 2026-11-28; standard:
findings/kaggle-gpu-sessions, checked 2026-11-28).

`--no-run` (saves a version without running it) and `--help` pass. It reads command text only, so a
push made inside a project's own script is not seen: such a runner calls the shared tool itself. A
guardrail against mistakes, not a security boundary; it fails open on anything it cannot parse.
"""

from __future__ import annotations

import json
import sys

from gpu_guard import _name, _segments, _strip_wrappers
from ram_guard import _unwrap

_REFUSED = (
    "Refused: `{cmd}` pushes without checking for an active version of this kernel. Run "
    "`python ~/claude-config/scripts/kaggle_slots.py push -p <folder>` in the background: it waits "
    "until the kernel has no queued or running version. (Rule: working-rules, \"Kaggle pushes\".)"
)
_ALLOWED = {"--no-run", "-h", "--help"}


def refusal(command: str) -> str:
    for words in _segments(command):
        words = _unwrap(_strip_wrappers(words))
        if words and _name(words[0]) == "uvx":
            words = words[1:]
        if len(words) < 3 or _name(words[0]) != "kaggle":
            continue
        if words[1] in {"kernels", "k"} and words[2] in {"push", "update"}:
            if not _ALLOWED & set(words[3:]):
                return _REFUSED.format(cmd=" ".join(words)[:100])
    return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") not in ("Bash", "PowerShell"):
        return 0
    tool_input = payload.get("tool_input")
    command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
    if "kaggle" not in command:
        return 0
    try:
        reason = refusal(command)
    except Exception:  # noqa: BLE001 (never block on a bug in the guard itself)
        return 0
    if reason:
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
