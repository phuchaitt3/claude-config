"""PreToolUse hook: keep chats started in other folders out of a repository that is in skim mode.

Skim mode is a study mode a project defines for itself: the user types `skim on`, and the project's own
hooks then limit what its chats may edit. Those hooks do not run in a chat started in another folder, so
such a chat could still change the project's pages (user's decision, 2026-11-25).

The project lists its folder in `~/.claude/skim-mode-roots.json` (a JSON list) and keeps the flag file
`.claude/skim-mode` while the mode is on. With no list, this hook returns at once. While a listed folder
has the flag, a chat whose project folder is not that folder is refused:
- Edit, Write, MultiEdit and NotebookEdit of a file inside it;
- a shell command run inside it or naming its path (reading too: command text does not show reliably
  what is only read; the Read, Grep and Glob tools still work).

It reads command text only, so a script that builds the path itself is not seen: a guardrail against
mistakes, not a security boundary. It fails open on anything it cannot read (standard:
findings/agent-permission-enforcement, checked 2026-11-05).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REGISTRY = Path.home() / ".claude" / "skim-mode-roots.json"
_EDITS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
_SHELLS = {"Bash", "PowerShell", "Monitor"}


def norm(path: str) -> str:
    """Lower case, forward slashes, `/d/x` and `d:/x` alike, no trailing slash."""
    p = re.sub(r"[\\/]+", "/", str(path)).lower()
    return re.sub(r"^/([a-z])(?=/|$)", r"\1:", p).rstrip("/")


def _inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root + "/")


def flagged_roots(registry: Path = REGISTRY) -> list[str]:
    roots = json.loads(registry.read_text(encoding="utf-8"))
    return [r for r in roots if isinstance(r, str) and (Path(r) / ".claude" / "skim-mode").exists()]


def names_root(command: str, root: str) -> bool:
    """True when the command text holds the folder's path, in any spelling, or its last two parts."""
    text = re.sub(r"[\\/]+", "/", command).lower()
    text = re.sub(r"(?<![\w.:/])/([a-z])(?=/)", r"\1:", text)
    tail = "/".join(root.split("/")[-2:])
    return any(re.search(rf"(?<![\w.-]){re.escape(x)}(?![\w.-])", text) for x in {root, tail})


def refusal(payload: dict, project_dir: str, roots: list[str]) -> str:
    tool = payload.get("tool_name")
    args = payload.get("tool_input")
    if not isinstance(args, dict) or (tool not in _EDITS and tool not in _SHELLS):
        return ""
    cwd = str(payload.get("cwd") or project_dir or "")
    for original in roots:
        root = norm(original)
        if project_dir and norm(project_dir) == root:
            continue  # the project's own hooks apply there
        if tool in _EDITS:
            path = str(args.get("file_path") or args.get("notebook_path") or "")
            path = path if re.match(r"^([A-Za-z]:|[\\/])", path) else os.path.join(cwd, path)
            hit = _inside(norm(os.path.normpath(path)), root)
        else:
            hit = _inside(norm(cwd), root) or names_root(str(args.get("command") or ""), root)
        if hit:
            return (f"Refused: {original} is in skim mode (the user is studying there), so a chat started in another "
                    "folder may not edit it or run shell commands in it. Read it with the Read, Grep or Glob tool if "
                    "you must; keep the change until the user types `skim off` there. Do not look for another way.")
    return ""


def main() -> int:
    try:
        if not REGISTRY.exists():
            return 0
        payload = json.load(sys.stdin)
        reason = refusal(payload, os.environ.get("CLAUDE_PROJECT_DIR", ""), flagged_roots())
    except Exception:  # never block on a bug in the guard itself
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
