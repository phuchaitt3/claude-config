"""PreToolUse hook: refuse a config-repo commit that cites a register entry that does not exist.

A point checked against industry practice carries `(standard: standards/<topic>, checked DATE)`, and
the finding lives in `standards/<topic>.md` (rules/working-rules.md, "Industry practice"). A tag with
no entry means the next chat finds nothing and searches again. This hook reads the added lines of the
staged diff in a repository that has `plugins/workflow/` and `standards/` (the config repo) and
denies the commit when a `standards/<topic>` reference has no `standards/<topic>.md` file. URLs such
as `.../standards/architecture-decisions.html` are not references: the name must not follow `/`, `.`,
`-` or a word character.

Fails open: any error prints nothing and exits 0.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

_COMMIT = re.compile(r"\bgit\b(?:\s+-\S+(?:\s+\S+)?)*\s+commit\b")
_CD = re.compile(r"\b(?:cd|pushd|Set-Location|sl)\s+(?:\"([^\"]+)\"|'([^']+)'|([^\s;&|]+))")
_REF = re.compile(r"(?<![\w/.-])standards/([a-z0-9][a-z0-9-]*)(?![\w/-]*\.\w)")
_PLACEHOLDER = {"topic"}


def workdir(command: str, cwd: str) -> str:
    found = _CD.findall(command)
    if not found:
        return cwd
    target = next(part for part in found[-1] if part)
    return str((Path(cwd) / Path(target).expanduser()).resolve())


def git(args: list[str], cwd: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=4, check=False
    )
    return result.stdout if result.returncode == 0 else ""


def missing_entries(added_lines: list[str], register: Path) -> list[str]:
    """Topics cited in the added lines that have no `<topic>.md` in the register folder."""
    topics = {m.group(1) for line in added_lines for m in _REF.finditer(line)}
    return sorted(t for t in topics - _PLACEHOLDER if not (register / f"{t}.md").is_file())


def check(command: str, cwd: str) -> list[str]:
    if not _COMMIT.search(command):
        return []
    folder = workdir(command, cwd)
    top = git(["rev-parse", "--show-toplevel"], folder).strip()
    if not top or not (Path(top) / "plugins" / "workflow").is_dir() or not (Path(top) / "standards").is_dir():
        return []
    diff = git(["diff", "--cached", "-U0", "--no-color"], folder).splitlines()
    added = [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")]
    return missing_entries(added, Path(top) / "standards")


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
        missing = check(command, str(payload.get("cwd") or "."))
    except Exception:  # never get in the way of a commit
        return 0
    if missing:
        names = ", ".join(f"standards/{t}" for t in missing)
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"This commit cites {names}, but no such entry exists in standards/. Add the entry "
                "(question, finding, sources, limits, date) and list it in standards/README.md in "
                "this commit, or fix the tag. A tag with no entry makes the next chat search again."
            ),
        }}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
