"""SessionStart hook: name a new chat `<repo>-<folder>-<id>` so `ListAgents` shows its repository.

Projects use the layout `<repo>/main` plus `<repo>/<ID>-<slug>` worktrees (`workflow:new-project`),
so the default chat name, taken from the working folder, was `main-..` in every repository and
peers could not tell which repository a chat was in (user's decision, 2026-11-10). On a new
session (`source` "startup") this hook sets the session title (Claude Code docs, hooks reference,
SessionStart: `sessionTitle`) to the folder label below plus the first two characters of the
session ID, which keeps two chats in one folder apart. Resumed, cleared and compacted sessions keep
their title. `focus_title` uses the same label.

Label: `<parent>-<folder>` when the folder is `main` or sits beside a `main` folder (the layout
above), otherwise the folder name alone.

Fails open: any error prints nothing and exits 0.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def _clean(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")


def folder_label(cwd: str) -> str:
    """`<repo>-<folder>` inside the `<repo>/main` layout, else the folder name; "chat" if empty."""
    if not cwd:
        return "chat"
    path = Path(cwd)
    name = _clean(path.name)
    parent = _clean(path.parent.name) if path.parent != path else ""
    in_layout = path.name == "main" or (path.parent / "main").is_dir()
    if in_layout and parent and name:
        return f"{parent}-{name}"
    return name or "chat"


def title_for(source: str, cwd: str, session_id: str) -> str | None:
    """The title for a new session, or None for a resumed, cleared or compacted one."""
    if source != "startup":
        return None
    suffix = _clean(session_id)[:2]
    label = folder_label(cwd)
    return f"{label}-{suffix}" if suffix else label


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    title = title_for(
        str(payload.get("source") or ""),
        str(payload.get("cwd") or ""),
        str(payload.get("session_id") or ""),
    )
    if title:
        output = {"hookSpecificOutput": {"hookEventName": "SessionStart", "sessionTitle": title}}
        print(json.dumps(output))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken hook must never block the session
        pass
