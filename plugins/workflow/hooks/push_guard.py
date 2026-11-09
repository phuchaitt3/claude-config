"""PreToolUse hook: refuse a force-push, a push to the default branch, and a push to a merged branch.

- Force in any form (`--force`, `-f`, `--force-with-lease`, `--mirror`, a `+` refspec) is refused
  everywhere: the working rules ban it in every tier.
- A push to the default branch is refused unless the repository is the config repo `~/claude-config`,
  its CLAUDE.md declares the direct tier, or the user opted it in with the local git setting
  `git config claude.pushDefault allow` (for private notes repositories; it stays out of every
  committed file, so no private path reaches the public config repo). Those are the working rules'
  exceptions. The user runs any other such push.
- A merge takes only what was on the branch at that moment, so a later push is lost. For a push to a
  branch: open PR -> allow; merged and none open -> deny; no PR, or gh unavailable -> allow.

All of it fails open: this guards against known mistakes and is not a security boundary (standard:
standards/agent-permission-enforcement, checked 2026-11-05).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from _gitcmd import GitCall, default_branch, git_calls

_DEFAULT_BRANCHES = {"main", "master"}
_SHORT_FORCE = re.compile(r"-[a-zA-Z]*f[a-zA-Z]*")
_DIRECT_TIER = re.compile(r"tier:\s*\**\s*direct", re.I)
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
    for call in git_calls(command, cwd):
        if call.subcommand != "push":
            continue
        directory, rest = call.directory, call.args
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


def _forces(args: Sequence[str]) -> bool:
    for arg in args:
        if arg in ("--force", "--force-if-includes", "--mirror"):
            return True
        if arg.startswith("--force-with-lease") or _SHORT_FORCE.fullmatch(arg):
            return True
        if arg.startswith("+") and len(arg) > 1:
            return True
    return False


def may_push_default(directory: str) -> bool:
    """True in the repositories where the rules let agents push the default branch."""
    try:
        top = _run(["git", "rev-parse", "--show-toplevel"], directory).strip()
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return True  # fail open
    config = str(Path.home() / "claude-config")
    if os.path.normcase(os.path.normpath(top)) == os.path.normcase(os.path.normpath(config)):
        return True
    try:
        if _DIRECT_TIER.search(Path(top, "CLAUDE.md").read_text(encoding="utf-8")):
            return True
    except OSError:
        pass
    return _opted_in(top)


def _opted_in(top: str) -> bool:
    """The user's per-repository opt-in: `git config claude.pushDefault allow` (local, uncommitted)."""
    try:
        value = _run(["git", "config", "--get", "claude.pushDefault"], top)
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return False
    return value.strip().lower() == "allow"


def _targets_default(call: GitCall) -> bool:
    """True when this `git push` reaches the default branch: by name, by --all or as the current."""
    try:
        names = _DEFAULT_BRANCHES | {default_branch(call.directory)}
        if "--all" in call.args or "--branches" in call.args:
            return True
        positional: list[str] = []
        skip = False
        for arg in call.args:
            if skip:
                skip = False
            elif arg in _VALUE_FLAGS:
                skip = True
            elif not arg.startswith("-"):
                positional.append(arg)
        specs = positional[1:]  # positional[0] is the remote
        if not specs:
            return _run(["git", "branch", "--show-current"], call.directory).strip() in names
        for spec in specs:
            target = spec.lstrip("+").split(":")[-1].removeprefix("refs/heads/")
            if target == "HEAD":
                target = _run(["git", "branch", "--show-current"], call.directory).strip()
            if target in names:
                return True
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return False  # fail open
    return False


def policy_refusal(
    command: str, cwd: str, may_push: Callable[[str], bool] = may_push_default
) -> str | None:
    """Why the rules ban this push whatever the state of its branch's PR, or None."""
    for call in git_calls(command, cwd):
        if call.subcommand != "push":
            continue
        if _forces(call.args):
            return "Force-pushing is banned in every project. If history must change, the user does it."
        if _targets_default(call) and not may_push(call.directory):
            return (
                "Pushing to the default branch is banned here: work on a feature branch and open a "
                "PR. If the user has approved this push, the user runs it."
            )
    return None


def check(command: str, cwd: str, state_fn: StateFn = pr_state_of_branch) -> str | None:
    """A refusal reason for a push to a branch whose PR already merged, or None."""
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
        cwd = str(payload.get("cwd") or ".")
        reason = policy_refusal(command, cwd) or check(command, cwd)
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
