"""Keep a multi-chat project's main checkout on the default branch and current; refuse git work there.

Every chat starts in the main checkout and reads its files, but all merges happen on GitHub, so
nothing moved it forward and chats answered from stale files; chats also switched it to branches
and committed there, against a rule that existed only as text (multi-chat skill, "Working rules").
Acts only where the main checkout has a handoff folder (the multi-chat opt-in). By hook event:

- SessionStart, UserPromptSubmit (at most every 5 minutes per repository): start a detached
  `refresh`, which fetches and fast-forwards the main checkout when that is safe (clean tracked
  files; on the default branch, a detached HEAD or a branch already merged into it). Otherwise it
  leaves the checkout alone and records a warning, shown once per session.
- PreToolUse (Bash, PowerShell): deny git commands that commit or move HEAD in the main checkout.

Fails open everywhere: this guards against a known mistake; it is not a security boundary.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from _gitcmd import (
    CACHE_ROOT, git, git_calls, git_ok, is_main_checkout, main_checkout_of, opted_in,
    default_branch, repo_key, spawn_detached,
)

CACHE = CACHE_ROOT / "main_checkout"
PROMPT_INTERVAL_S = 5 * 60
START_INTERVAL_S = 60  # several hooks at one start, or a quick /clear, refresh once
GUARDED = {"commit", "merge", "rebase", "reset", "cherry-pick", "revert", "am", "switch",
           "checkout", "pull"}
_BRANCH_FLAGS = {"-b", "-B", "-c", "-C", "--detach", "--orphan", "--create", "--force-create"}


# --- refresh (runs detached) --------------------------------------------------------------------

def _behind(main: Path, target: str) -> str:
    try:
        return git(["rev-list", "--count", f"HEAD..{target}"], main).strip()
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return "?"


def refresh(main: Path) -> str | None:
    """Fast-forward `main` to origin's default branch when safe; else a warning for the chats."""
    branch_name = default_branch(main)
    target = f"origin/{branch_name}"
    if not git_ok(["fetch", "origin", "--quiet", "--prune"], main, timeout=60):
        return None  # offline or no remote: nothing to compare with, say nothing
    current = git(["branch", "--show-current"], main).strip()
    if git(["status", "--porcelain", "--untracked-files=no"], main).strip():
        why = "has uncommitted changes"
    elif current == branch_name:
        if git_ok(["merge", "--ff-only", "--quiet", target], main):
            return None
        why = f"has commits on `{branch_name}` that are not on `{target}`"
    elif git_ok(["merge-base", "--is-ancestor", "HEAD", target], main):
        if git_ok(["switch", "--quiet", branch_name], main) and git_ok(
            ["merge", "--ff-only", "--quiet", target], main
        ):
            return None
        why = f"could not be switched back to `{branch_name}`"
    else:
        why = f"is on `{current or 'a detached HEAD'}` with commits not on `{target}`"
    return (
        f"The main checkout {main} {why}, so the hook left it alone; it is {_behind(main, target)} "
        f"commits behind `{target}` and its files may be stale. Read repository content with "
        f"`git show {target}:<path>`, and do git work in a task worktree (multi-chat skill)."
    )


def _state_path(main: Path) -> Path:
    return CACHE / f"{repo_key(main)}.json"


def _load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def run_refresh(main: Path) -> None:
    warning = refresh(main)
    path = _state_path(main)
    state = _load(path)
    if warning != state.get("warning"):
        state = {"warning": warning, "shown": []}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")


# --- session start and prompts ------------------------------------------------------------------

def on_prompt(payload: dict, event: str, now: float) -> str | None:
    """Start a refresh when due; return a pending warning not yet shown in this session."""
    main = main_checkout_of(str(payload.get("cwd") or "."))
    if main is None or not opted_in(main):
        return None
    stamp = CACHE / f"{repo_key(main)}.stamp"
    interval = START_INTERVAL_S if event == "SessionStart" else PROMPT_INTERVAL_S
    try:
        due = now - stamp.stat().st_mtime >= interval
    except OSError:
        due = True
    if due:
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.touch()  # stamp first: a slow or failing refresh is not retried on every prompt
        spawn_detached([str(Path(__file__).resolve()), "refresh", str(main)])
    path = _state_path(main)
    state = _load(path)
    session = str(payload.get("session_id") or "")
    if not state.get("warning") or session in state.get("shown", []):
        return None
    state["shown"] = [*state.get("shown", []), session][-50:]
    path.write_text(json.dumps(state), encoding="utf-8")
    return str(state["warning"])


# --- the guard ----------------------------------------------------------------------------------

def check(command: str, cwd: str) -> str | None:
    """A refusal reason for `command`, or None when it may run."""
    for call in git_calls(command, cwd):
        if call.subcommand not in GUARDED:
            continue
        try:
            if not is_main_checkout(call.directory):
                continue
            main = main_checkout_of(call.directory)
            if main is None or not opted_in(main):
                continue
            branch_name = default_branch(main)
            positional = [a for a in call.args if not a.startswith("-")]
            if call.subcommand in ("switch", "checkout") and positional == [branch_name] and not (
                _BRANCH_FLAGS & set(call.args)
            ):
                continue
            if call.subcommand == "pull" and "--ff-only" in call.args and (
                git(["branch", "--show-current"], call.directory).strip() == branch_name
            ):
                continue
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            continue  # fail open
        return (
            f"`git {call.subcommand}` would change the main checkout ({main}), which stays on "
            f"`{branch_name}` so every chat reads current files (multi-chat skill, \"Working "
            f"rules\"). Do this in a task worktree: `git fetch origin`, then `git worktree add "
            f"../<ID>-<slug> -b <branch> origin/{branch_name}`, and run it there."
        )
    return None


def main() -> int:
    if sys.argv[1:2] == ["refresh"] and len(sys.argv) == 3:
        run_refresh(Path(sys.argv[2]))
        return 0
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    event = str(payload.get("hook_event_name") or "")
    if event == "PreToolUse":
        if payload.get("tool_name") not in ("Bash", "PowerShell"):
            return 0
        tool_input = payload.get("tool_input")
        command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
        if "git" not in command:
            return 0
        reason = check(command, str(payload.get("cwd") or "."))
        if reason:
            json.dump({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }}, sys.stdout)
    elif event in ("SessionStart", "UserPromptSubmit"):
        warning = on_prompt(payload, event, time.time())
        if warning:
            json.dump({"hookSpecificOutput": {
                "hookEventName": event, "additionalContext": warning,
            }}, sys.stdout)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # a broken hook must never get in the way of a session
        sys.exit(0)
