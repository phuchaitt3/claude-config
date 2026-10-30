"""PreToolUse hook: refuse `git push` to a branch whose pull request is already merged.

A merge takes only what was on the branch at that moment, so a later push is lost (working rules,
"Commits"). Chats forget which of their PRs merged; this checks GitHub at the moment of the push,
so it needs no notification to have arrived. It looks at the PR of the branch being pushed:
open -> allow; merged and none open -> deny; no PR, or gh unavailable -> allow (fail open, this is
a guard against a known mistake, not a security boundary).
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from collections.abc import Callable, Sequence

_SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|&\n()`]")
_DEFAULT_BRANCHES = {"main", "master"}
# `git push` flags that take a separate value.
_VALUE_FLAGS = {"--repo", "--receive-pack", "--exec", "-o", "--push-option", "--signed"}

StateFn = Callable[[str, str], str]


def _run(args: Sequence[str], cwd: str) -> str:
    result = subprocess.run(
        list(args), cwd=cwd or ".", capture_output=True, text=True, encoding="utf-8",
        timeout=8, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip()[:200])
    return result.stdout


def pr_state_of_branch(branch: str, cwd: str) -> str:
    """'open', 'merged' or 'none' for the PRs whose head is `branch`; raises on gh failure."""
    prs = json.loads(
        _run(["gh", "pr", "list", "--head", branch, "--state", "all",
              "--json", "number,state", "--limit", "10"], cwd)
    )
    states = {pr["state"] for pr in prs}
    if "OPEN" in states:
        return "open"
    return "merged" if "MERGED" in states else "none"


def pushed_branches(command: str, cwd: str) -> list[tuple[str, str]]:
    """(branch, directory) for each `git push` in `command` that pushes a named or current branch."""
    found: list[tuple[str, str]] = []
    for segment in _SEGMENT_SPLIT.split(command):
        try:
            tokens = shlex.split(segment, posix=True)
        except ValueError:
            tokens = segment.split()
        if not tokens or tokens[0].replace("\\", "/").rsplit("/", 1)[-1].lower() not in (
            "git", "git.exe"
        ):
            continue
        directory, i = cwd, 1
        while i < len(tokens) and tokens[i].startswith("-"):  # git global options
            if tokens[i] == "-C" and i + 1 < len(tokens):
                directory, i = tokens[i + 1], i + 2
            else:
                i += 2 if tokens[i] in ("-c", "--git-dir", "--work-tree") else 1
        if tokens[i : i + 1] != ["push"]:
            continue
        rest = tokens[i + 1 :]
        if any(a in ("--delete", "-d", "--tags", "--all", "--mirror") for a in rest):
            continue
        positional: list[str] = []
        skip = False
        for arg in rest:
            if skip:
                skip = False
            elif arg in _VALUE_FLAGS:
                skip = True
            elif not arg.startswith("-"):
                positional.append(arg)
        refspecs = positional[1:]  # positional[0] is the remote
        if not refspecs:
            found.append(("", directory))  # current branch
        for spec in refspecs:
            target = spec.lstrip("+").split(":")[-1] if ":" in spec else spec.lstrip("+")
            target = target.removeprefix("refs/heads/")
            found.append(("" if target == "HEAD" else target, directory))
    return found


def check(command: str, cwd: str, state_fn: StateFn = pr_state_of_branch) -> str | None:
    """A refusal reason for `command`, or None when it may run."""
    for branch, directory in pushed_branches(command, cwd):
        try:
            name = branch or _run(["git", "branch", "--show-current"], directory).strip()
            if not name or name in _DEFAULT_BRANCHES:
                continue
            state = state_fn(name, directory)
        except (OSError, RuntimeError, ValueError, KeyError, subprocess.TimeoutExpired):
            continue  # fail open
        if state == "merged":
            return (
                f"Branch `{name}` belongs to a pull request that is already merged, and a merge "
                "takes only what was on the branch at that moment, so this push would be lost. "
                "Put the follow-up on a new branch off the default branch."
            )
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") not in ("Bash", "PowerShell"):
        return 0
    tool_input = payload.get("tool_input")
    command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
    if "push" not in command:
        return 0
    try:
        reason = check(command, str(payload.get("cwd") or "."))
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
