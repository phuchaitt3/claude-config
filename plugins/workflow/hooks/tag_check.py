"""PreToolUse hook: refuse a config-repo commit that cites a register entry that does not exist.

A point checked against industry practice carries `(standard: findings/<topic>, checked DATE)`, and
the finding lives in `findings/<topic>.md` (rules/working-rules.md, "Industry practice"). A tag with
no entry means the next chat finds nothing and searches again. This hook reads the added lines of the
staged diff in a repository that has `plugins/workflow/` and `findings/` (the config repo) and
denies the commit when a `findings/<topic>` reference has no `findings/<topic>.md` file. The register
folder was called `standards/` until 2026-11-13; that prefix is still accepted and resolved against
`findings/`, because tags in other repositories were not rewritten. URLs such as
`.../standards/architecture-decisions.html` are not references: the name must not follow `/`, `.`,
`-` or a word character.

The folder name is set once, in REGISTER_DIR.

A second, softer check runs in any repository (user's decision, 2026-11-15): a `standard:` tag that
cites an entry marked "Unverified" (findings/README.md, "Unverified entries": no Evidence strength
field, lines not marked sourced or inference) gets a reminder to recheck the entry before relying on it.
It never denies the commit. Outside the config repo the entry is read from `~/claude-config/findings`.

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
REGISTER_DIR = "findings"
LEGACY_DIRS = ("standards",)
_REF = re.compile(
    r"(?<![\w/.-])(?:" + "|".join(re.escape(d) for d in (REGISTER_DIR, *LEGACY_DIRS)) + r")/([a-z0-9][a-z0-9-]*)(?![\w/-]*\.\w)"
)
_PLACEHOLDER = {"topic"}
UNVERIFIED_MARK = "> **Unverified ("
HOME_REGISTER = Path.home() / "claude-config" / REGISTER_DIR


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


def unverified_entries(added_lines: list[str], register: Path) -> list[str]:
    """Topics cited by a `standard:` tag in the added lines whose entry carries the Unverified note."""
    topics = {m.group(1) for line in added_lines if "standard:" in line for m in _REF.finditer(line)}
    found = []
    for topic in sorted(topics - _PLACEHOLDER):
        entry = register / f"{topic}.md"
        if entry.is_file() and UNVERIFIED_MARK in entry.read_text(encoding="utf-8", errors="replace"):
            found.append(topic)
    return found


def _staged(command: str, cwd: str) -> tuple[Path, list[str], str] | None:
    """(repo top, added lines of the staged diff, folder) for a commit command, else None."""
    if not _COMMIT.search(command):
        return None
    folder = workdir(command, cwd)
    top = git(["rev-parse", "--show-toplevel"], folder).strip()
    if not top:
        return None
    diff = git(["diff", "--cached", "-U0", "--no-color"], folder).splitlines()
    added = [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")]
    return Path(top), added, folder


def _is_config_repo(top: Path) -> bool:
    return (top / "plugins" / "workflow").is_dir() and (top / REGISTER_DIR).is_dir()


def check(command: str, cwd: str) -> list[str]:
    staged = _staged(command, cwd)
    if staged is None or not _is_config_repo(staged[0]):
        return []
    top, added, _ = staged
    return missing_entries(added, top / REGISTER_DIR)


def check_unverified(command: str, cwd: str) -> list[str]:
    """Unverified entries cited in the staged diff of any repository."""
    staged = _staged(command, cwd)
    if staged is None:
        return []
    top, added, _ = staged
    register = top / REGISTER_DIR if _is_config_repo(top) else HOME_REGISTER
    return unverified_entries(added, register) if register.is_dir() else []


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
        unverified = [] if missing else check_unverified(command, str(payload.get("cwd") or "."))
    except Exception:  # never get in the way of a commit
        return 0
    if unverified:
        names = ", ".join(f"{REGISTER_DIR}/{t}" for t in unverified)
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": (
                f"This commit cites {names} in a `standard:` tag, but the entry is marked Unverified "
                f"(no Evidence strength field; lines not marked sourced or inference). Before relying on "
                f"it, recheck it as {REGISTER_DIR}/README.md, \"Unverified entries\", says: re-read its "
                f"sources or search, mark each line sourced or inference, add the field, remove the note. "
                f"Or reword the tag to say the point is unchecked."
            ),
        }}, sys.stdout)
        return 0
    if missing:
        names = ", ".join(f"{REGISTER_DIR}/{t}" for t in missing)
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"This commit cites {names}, but no such entry exists in {REGISTER_DIR}/. Add the entry "
                f"(question, finding, sources, limits, date) and list it in {REGISTER_DIR}/README.md in "
                f"this commit, or fix the tag. A tag with no entry makes the next chat search again."
            ),
        }}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
