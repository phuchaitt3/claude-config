"""UserPromptSubmit hook: name each chat after its repository, and `focus-...` in focus mode.

`ListAgents` names come from the working folder. In the `<repo>/main` layout every main checkout
gave `main-..`, so peers could not tell which repository a chat was in (user's decision,
2026-11-10). A focus chat (never a reviewer, see the `workflow:focus` skill) also needs its role in
the name, since peers pick reviewers from `ListAgents`.

This hook sets the session title (Claude Code docs, hooks reference, UserPromptSubmit decision
control: `sessionTitle`), which `ListAgents` then shows as the chat's name (tested 2026-11-10; a
SessionStart `sessionTitle` does not change the `ListAgents` name):
- on the first prompt of an untitled chat: `<label>-<first two characters of the session ID>`;
- when the prompt is "focus mode", "talk mode", "conversation chat", `/focus` or `/talk`:
  `focus-<label>`, unless the title already starts with `focus-`.
A chat that already has a title keeps it, so a user's `/rename` is never overwritten.

Label: `<parent>-<folder>` when the folder is `main` or sits beside a `main` folder (the layout
above), otherwise the folder name alone.

Fails open: any error prints nothing and exits 0.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TRIGGER = re.compile(r"^\s*(/focus|/talk|focus mode|talk mode|conversation chat)\b", re.IGNORECASE)
PREFIX = "focus-"


def _clean(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-")


def folder_label(cwd: str) -> str:
    """`<repo>-<folder>` inside the `<repo>/main` layout, else the folder name; "chat" if empty."""
    if not cwd:
        return "chat"
    path = Path(cwd)
    name = _clean(path.name)
    parent = _clean(path.parent.name) if path.parent != path else ""
    try:
        in_layout = path.name == "main" or (path.parent / "main").is_dir()
    except OSError:
        in_layout = False
    if in_layout and parent and name:
        return f"{parent}-{name}"
    return name or "chat"


def title_for(prompt: str, cwd: str, current_title: str, session_id: str = "") -> str | None:
    """The title to set, or None to leave the chat's title as it is."""
    if TRIGGER.match(prompt):
        if current_title.lower().startswith(PREFIX):
            return None
        return PREFIX + folder_label(cwd)
    if current_title.strip():
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
        str(payload.get("prompt") or ""),
        str(payload.get("cwd") or ""),
        str(payload.get("session_title") or ""),
        str(payload.get("session_id") or ""),
    )
    if title:
        output = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "sessionTitle": title}}
        print(json.dumps(output))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken hook must never block the session
        pass
