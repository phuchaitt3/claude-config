"""Shared helpers for the workflow hooks that read git commands and repositories.

- `git_calls` finds each `git` invocation in a shell command line and the folder it runs in
  (following `cd X &&` and `git -C X`), so guards look at the command, not at text that only
  mentions git.
- The repository helpers find a checkout's main checkout, tell whether a project uses several
  chats (it has a handoff folder), and start a detached background job so a hook never waits.
"""

from __future__ import annotations

import hashlib
import os
import re
import shlex
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

_SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|&\n()`]")
_CD = ("cd", "pushd", "set-location", "sl")
CACHE_ROOT = Path.home() / ".claude" / "hook-cache"
# Where the multi-chat skill puts the handoff folder; its presence opts a project in.
HANDOFF_DIRS = (Path(".handoff"), Path("data") / "handoff")


@dataclass(frozen=True)
class GitCall:
    directory: str
    subcommand: str
    args: tuple[str, ...]


def git_calls(command: str, cwd: str) -> list[GitCall]:
    """Every `git` invocation in `command`, with the folder it runs in and its subcommand."""
    found: list[GitCall] = []
    workdir = cwd
    for segment in _SEGMENT_SPLIT.split(command):
        try:
            tokens = shlex.split(segment, posix=True)
        except ValueError:
            tokens = segment.split()
        if len(tokens) >= 2 and tokens[0].lower() in _CD:
            workdir = os.path.normpath(os.path.join(workdir, tokens[1]))
            continue
        if not tokens or tokens[0].replace("\\", "/").rsplit("/", 1)[-1].lower() not in (
            "git", "git.exe"
        ):
            continue
        directory, i = workdir, 1
        while i < len(tokens) and tokens[i].startswith("-"):  # git global options
            if tokens[i] == "-C" and i + 1 < len(tokens):
                directory, i = os.path.normpath(os.path.join(workdir, tokens[i + 1])), i + 2
            else:
                i += 2 if tokens[i] in ("-c", "--git-dir", "--work-tree") else 1
        if i < len(tokens):
            found.append(GitCall(directory, tokens[i], tuple(tokens[i + 1 :])))
    return found


def git(args: Sequence[str], cwd: str | Path, timeout: float = 8) -> str:
    """stdout of `git <args>` in `cwd`; raises RuntimeError on a non-zero exit."""
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=timeout, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip()[:300])
    return result.stdout


def git_ok(args: Sequence[str], cwd: str | Path, timeout: float = 8) -> bool:
    try:
        git(args, cwd, timeout)
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return False
    return True


def _same(a: str, b: str) -> bool:
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))


def main_checkout_of(directory: str | Path) -> Path | None:
    """The main checkout of the repository `directory` belongs to, or None."""
    common = git(["rev-parse", "--path-format=absolute", "--git-common-dir"], directory).strip()
    path = Path(common)
    return path.parent if path.name == ".git" else None


def is_main_checkout(directory: str | Path) -> bool:
    """True when `directory` is inside a repository's main checkout, not a linked worktree."""
    out = git(["rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"], directory)
    lines = out.strip().splitlines()
    return len(lines) == 2 and _same(lines[0], lines[1])


def opted_in(main: Path) -> bool:
    return any((main / d).is_dir() for d in HANDOFF_DIRS)


def default_branch(main: str | Path) -> str:
    try:
        ref = git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], main).strip()
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return "main"
    return ref.removeprefix("origin/") or "main"


def repo_key(main: Path) -> str:
    return hashlib.sha1(os.path.normcase(str(main)).encode()).hexdigest()[:8]


def spawn_detached(args: Sequence[str]) -> None:
    """Start `python <args>` in the background, outliving the hook, with no console window."""
    kwargs: dict = {
        "stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL, "close_fds": True,
    }
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        try:
            subprocess.Popen(
                [sys.executable, *args],
                creationflags=flags | 0x01000000,  # CREATE_BREAKAWAY_FROM_JOB
                **kwargs,
            )
            return
        except OSError:  # the job forbids breakaway: start it inside the job instead
            kwargs["creationflags"] = flags
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen([sys.executable, *args], **kwargs)
