"""SessionStart hook: tell the chat to load `workflow:multi-chat` when the repository has a handoff folder.

Skills load by the model matching a description, which is the weak point: a chat can read "use the
multi-chat skill" in a project's CLAUDE.md and still skip it. A hook runs every time, so this one
adds the instruction to the context at session start (also after /clear and compaction). It works
from the main checkout, so a worktree finds the same `.handoff/` folder.

Fails open: outside a git repo, or on any error, it prints nothing and exits 0.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main_checkout(cwd: Path) -> Path | None:
    """The main checkout's folder, from any worktree of the repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=3, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    common = result.stdout.strip()
    return Path(common).parent if result.returncode == 0 and common else None


def handoff_folder(root: Path) -> Path | None:
    """The handoff folder: `.handoff/`, or any folder with an INBOX.md that CLAUDE.md names."""
    candidate = root / ".handoff"
    if candidate.is_dir():
        return candidate
    if (root / "INBOX.md").is_file():
        return root
    return None


def message(folder: Path) -> str:
    return (
        f"This repository has a handoff folder (`{folder}`). Before any other work, load the "
        "`workflow:multi-chat` skill and follow its \"At the start of a chat\" steps."
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    root = main_checkout(Path(payload.get("cwd") or "."))
    folder = handoff_folder(root) if root else None
    if folder is None:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": message(folder),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken hook must never block the session
        pass
