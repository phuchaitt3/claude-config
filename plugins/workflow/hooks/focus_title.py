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

Task in the name (user's decision, 2026-11-20): Claude Code writes its own generated title into the
session transcript (`{"type":"ai-title","aiTitle":"..."}`, near the start of the file; internal,
undocumented format: standard: findings/claude-code-session-naming, checked 2026-11-20). On a
later prompt, when the chat's title is still exactly the one this hook set (`<label>-<id>`), the
title becomes `<label>: <aiTitle>`, so peers see both where the chat was launched and what it does.
Any other title (a rename, a focus title, an already combined one) is left alone, and a missing or
unreadable transcript keeps the repo title. The combined title is a custom title, so it stops
following later generated titles.

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


def repo_title(cwd: str, session_id: str = "") -> str:
    """The title this hook gives an untitled chat: `<label>-<first two ID characters>`."""
    suffix = _clean(session_id)[:2]
    label = folder_label(cwd)
    return f"{label}-{suffix}" if suffix else label


def read_ai_title(transcript_path: str, max_bytes: int = 1_000_000) -> str:
    """The latest generated title in the first `max_bytes` of the transcript, or "" if none."""
    if not transcript_path:
        return ""
    found = ""
    read = 0
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                read += len(line)
                if read > max_bytes:
                    break
                if '"ai-title"' not in line:
                    continue
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if isinstance(entry, dict) and entry.get("type") == "ai-title":
                    found = str(entry.get("aiTitle") or "")
    except OSError:
        return ""
    return re.sub(r"\s+", " ", found).strip()[:60]


def title_for(
    prompt: str, cwd: str, current_title: str, session_id: str = "", ai_title: str = ""
) -> str | None:
    """The title to set, or None to leave the chat's title as it is."""
    if TRIGGER.match(prompt):
        if current_title.lower().startswith(PREFIX):
            return None
        return PREFIX + folder_label(cwd)
    base = repo_title(cwd, session_id)
    if current_title.strip():
        if ai_title and current_title == base:
            return f"{folder_label(cwd)}: {ai_title}"
        return None
    return base


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    prompt = str(payload.get("prompt") or "")
    cwd = str(payload.get("cwd") or "")
    current = str(payload.get("session_title") or "")
    session_id = str(payload.get("session_id") or "")
    ai_title = ""
    if current and current == repo_title(cwd, session_id) and not TRIGGER.match(prompt):
        ai_title = read_ai_title(str(payload.get("transcript_path") or ""))
    title = title_for(prompt, cwd, current, session_id, ai_title)
    if title:
        output = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "sessionTitle": title}}
        print(json.dumps(output))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken hook must never block the session
        pass
