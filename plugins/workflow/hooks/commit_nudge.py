"""PreToolUse hook: when committing a plugin change in the config repo, ask whether it is critical.

A change under `plugins/` reaches running chats only when the user types `/reload-plugins`. The
author decides whether that is urgent; if it is, `plugins/workflow/critical.json` goes into the same
commit and `plugin_notice.py` tells every running chat once. This hook only reminds, it never
blocks. It fires on a `git commit` whose command text has the word `plugins` or whose staged files are
under it, in a repository that has `plugins/workflow/` (the config repo). It cannot see files that
`git commit -a` would stage.

Fails open: any error prints nothing and exits 0.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REMINDER = (
    "This commit changes the config repo's plugins. Is the update critical, meaning a running chat on "
    "the old text would act wrongly in a way that is hard to undo or breaks coordination (a hard "
    "limit, merge or push gate, registry or messaging rule)? If yes, set version, since and why in "
    "`plugins/workflow/critical.json` in this same commit; running chats are then told once to have "
    "the user type `/reload-plugins`. If no, leave it: they pick the change up at their next new session."
)

_COMMIT = re.compile(r"\bgit\b(?:\s+-\S+(?:\s+\S+)?)*\s+commit\b")
_PLUGINS = re.compile(r"\bplugins\b")
_CD = re.compile(r"\b(?:cd|pushd|Set-Location|sl)\s+(?:\"([^\"]+)\"|'([^']+)'|([^\s;&|]+))")


def workdir(command: str, cwd: str) -> str:
    """The folder the commit runs in: the last `cd X` in the command, else the hook's cwd."""
    found = _CD.findall(command)
    if not found:
        return cwd
    target = next(part for part in found[-1] if part)
    return str((Path(cwd) / Path(target).expanduser()).resolve())


def git(args: list[str], cwd: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=3, check=False
    )
    return result.stdout if result.returncode == 0 else ""


def needs_reminder(command: str, cwd: str) -> bool:
    if not _COMMIT.search(command):
        return False
    folder = workdir(command, cwd)
    top = git(["rev-parse", "--show-toplevel"], folder).strip()
    if not top or not (Path(top) / "plugins" / "workflow").is_dir():
        return False
    staged = git(["diff", "--cached", "--name-only"], folder).splitlines()
    return bool(_PLUGINS.search(command)) or any(name.startswith("plugins/") for name in staged)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") not in ("Bash", "PowerShell"):
        return 0
    tool_input = payload.get("tool_input")
    command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
    if "commit" not in command:
        return 0
    try:
        remind = needs_reminder(command, str(payload.get("cwd") or "."))
    except Exception:  # never get in the way of a commit
        return 0
    if remind:
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "additionalContext": REMINDER,
        }}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
