"""Keep main checkouts current; in multi-chat projects also keep them on the default branch.

Every chat starts in the main checkout and reads its files, but all merges happen on GitHub, so
nothing moved it forward and chats answered from stale files; chats also switched it to branches
and committed there, against a rule that existed only as text (multi-chat skill, "Working rules").
A chat working in one repository also reads others (results from another project) and
answered from a checkout one merged PR behind (user's decision, 2026-11-09: refresh every
repository, not only multi-chat ones, and any repository a chat reads from). By hook event:

- SessionStart, UserPromptSubmit (at most every 5 minutes per repository): start a detached
  `refresh` of the session's own repository, which fetches and fast-forwards the main checkout
  when that is safe (clean tracked files; on the default branch, or in a multi-chat project a
  detached HEAD or a branch already merged into it). Otherwise it leaves the checkout alone and
  records a warning, shown once per session.
- PreToolUse (Read, Grep, Glob, Bash, PowerShell): for each path in the call that lies in another
  repository's main checkout, refresh that checkout first (synchronously, same 5-minute limit) and
  pass on its warning once per session.
- PreToolUse (Bash, PowerShell), multi-chat projects only (a handoff folder): deny git commands
  that commit or move HEAD in the main checkout.

Fails open everywhere: this guards against a known mistake; it is not a security boundary.
"""

from __future__ import annotations

import json
import os
import re
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
READ_FETCH_TIMEOUT_S = 10  # a read waits for this fetch; hooks.json gives the hook 20 s
MAX_READ_PATHS = 6
READ_TOOLS = {"Read": "file_path", "Grep": "path", "Glob": "path"}
SHELL_TOOLS = ("Bash", "PowerShell")
# Absolute paths in a shell command: C:\x or C:/x, Git Bash's /c/x, and ~/x.
_STOP = "\\s\"'`;|&<>()"
_WIN_PATH = re.compile(rf"(?<![\w/])([A-Za-z]:[\\/][^{_STOP}]*)")
_MSYS_PATH = re.compile(rf"(?<![\w./~-])/([A-Za-z])/([^{_STOP}]*)")
_HOME_PATH = re.compile(rf"(?<![\w/])~[\\/]([^{_STOP}]*)")
GUARDED = {"commit", "merge", "rebase", "reset", "cherry-pick", "revert", "am", "switch",
           "checkout", "pull"}
_BRANCH_FLAGS = {"-b", "-B", "-c", "-C", "--detach", "--orphan", "--create", "--force-create"}


# --- refresh (runs detached) --------------------------------------------------------------------

def _behind(main: Path, target: str) -> str:
    try:
        return git(["rev-list", "--count", f"HEAD..{target}"], main).strip()
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return "?"


def refresh(main: Path, fetch_timeout: float = 60) -> str | None:
    """Fast-forward `main` to origin's default branch when safe; else a warning for the chats.

    In a multi-chat project the main checkout belongs on the default branch, so the refresh also
    returns it there from a merged branch and warns about any other state. Elsewhere it is the
    user's working folder: it never switches branches and warns only when the checkout is behind.
    """
    multi_chat = opted_in(main)
    branch_name = default_branch(main)
    target = f"origin/{branch_name}"
    if not git_ok(["fetch", "origin", "--quiet", "--prune"], main, timeout=fetch_timeout):
        return None  # offline or no remote: nothing to compare with, say nothing
    behind = _behind(main, target)
    if not multi_chat and behind in ("0", "?"):
        return None
    current = git(["branch", "--show-current"], main).strip()
    if git(["status", "--porcelain", "--untracked-files=no"], main).strip():
        why = "has uncommitted changes"
    elif current == branch_name:
        if git_ok(["merge", "--ff-only", "--quiet", target], main):
            return None
        why = f"has commits on `{branch_name}` that are not on `{target}`"
    elif multi_chat and git_ok(["merge-base", "--is-ancestor", "HEAD", target], main):
        if git_ok(["switch", "--quiet", branch_name], main) and git_ok(
            ["merge", "--ff-only", "--quiet", target], main
        ):
            return None
        why = f"could not be switched back to `{branch_name}`"
    else:
        why = f"is on `{current or 'a detached HEAD'}`, not `{branch_name}`"
    advice = ", and do git work in a task worktree (multi-chat skill)." if multi_chat else "."
    return (
        f"The main checkout {main} {why}, so the hook left it alone; it is {behind} "
        f"commits behind `{target}` and its files may be stale. Read repository content with "
        f"`git show {target}:<path>`{advice}"
    )


def _state_path(main: Path) -> Path:
    return CACHE / f"{repo_key(main)}.json"


def _load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def run_refresh(main: Path, fetch_timeout: float = 60) -> None:
    warning = refresh(main, fetch_timeout)
    path = _state_path(main)
    state = _load(path)
    if warning != state.get("warning"):
        state = {"warning": warning, "shown": []}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")


def _claim_refresh(main: Path, interval: float, now: float) -> bool:
    """True when `main` is due a refresh. Stamps it first, so a slow or failing refresh is not
    retried on every prompt or read."""
    stamp = CACHE / f"{repo_key(main)}.stamp"
    try:
        if now - stamp.stat().st_mtime < interval:
            return False
    except OSError:
        pass
    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.touch()
    return True


def _pending_warning(main: Path, session: str) -> str | None:
    """The warning recorded for `main`, once per session."""
    path = _state_path(main)
    state = _load(path)
    if not state.get("warning") or session in state.get("shown", []):
        return None
    state["shown"] = [*state.get("shown", []), session][-50:]
    path.write_text(json.dumps(state), encoding="utf-8")
    return str(state["warning"])


# --- session start and prompts ------------------------------------------------------------------

def on_prompt(payload: dict, event: str, now: float) -> str | None:
    """Start a refresh when due; return a pending warning not yet shown in this session."""
    main = main_checkout_of(str(payload.get("cwd") or "."))
    if main is None:
        return None
    interval = START_INTERVAL_S if event == "SessionStart" else PROMPT_INTERVAL_S
    if _claim_refresh(main, interval, now):
        spawn_detached([str(Path(__file__).resolve()), "refresh", str(main)])
    return _pending_warning(main, str(payload.get("session_id") or ""))


# --- reads from other repositories --------------------------------------------------------------

def paths_in(tool_name: str, tool_input: dict) -> list[str]:
    """Absolute paths a tool call reads: its path field, or absolute paths in a shell command."""
    if tool_name in READ_TOOLS:
        value = tool_input.get(READ_TOOLS[tool_name])
        return [value] if isinstance(value, str) and value else []
    if tool_name not in SHELL_TOOLS:
        return []
    command = str(tool_input.get("command") or "")
    found = [m.group(1) for m in _WIN_PATH.finditer(command)]
    if os.name == "nt":
        found += [f"{m.group(1).upper()}:/{m.group(2)}" for m in _MSYS_PATH.finditer(command)]
    found += [str(Path.home() / m.group(1)) for m in _HOME_PATH.finditer(command)]
    return found


def _existing_dir(path: str) -> Path | None:
    current = Path(os.path.expanduser(path))
    for candidate in (current, *current.parents):
        if candidate.is_dir():
            return candidate
    return None


def _key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def foreign_main_checkouts(paths: list[str], cwd: str) -> list[Path]:
    """Main checkouts, other than the session's own repository's, that `paths` lie in.

    A linked worktree is skipped: it is a task branch, which its chat keeps current itself."""
    try:
        own = main_checkout_of(cwd)
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        own = None
    seen: dict[str, Path] = {}
    for path in paths[:MAX_READ_PATHS]:
        directory = _existing_dir(path)
        if directory is None:
            continue
        try:
            if not is_main_checkout(directory):
                continue
            main = main_checkout_of(directory)
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            continue
        if main is None or (own is not None and _key(main) == _key(own)):
            continue
        seen.setdefault(_key(main), main)
    return list(seen.values())


def on_read(payload: dict, now: float) -> str | None:
    """Refresh each other repository the call reads, when due; return their pending warnings."""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    paths = paths_in(str(payload.get("tool_name") or ""), tool_input)
    if not paths:
        return None
    session = str(payload.get("session_id") or "")
    warnings = []
    for main in foreign_main_checkouts(paths, str(payload.get("cwd") or ".")):
        if _claim_refresh(main, PROMPT_INTERVAL_S, now):
            run_refresh(main, READ_FETCH_TIMEOUT_S)
        warning = _pending_warning(main, session)
        if warning:
            warnings.append(warning)
    return " ".join(warnings) or None


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
        tool_input = payload.get("tool_input")
        if payload.get("tool_name") in SHELL_TOOLS and isinstance(tool_input, dict):
            command = str(tool_input.get("command", ""))
            reason = check(command, str(payload.get("cwd") or ".")) if "git" in command else None
            if reason:
                json.dump({"hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }}, sys.stdout)
                return 0
        warning = on_read(payload, time.time())
        if warning:
            json.dump({"hookSpecificOutput": {
                "hookEventName": "PreToolUse", "additionalContext": warning,
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
