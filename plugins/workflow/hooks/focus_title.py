"""UserPromptSubmit hook: name a chat `focus-<folder>` when the user starts focus mode.

Peers pick a reviewer from `ListAgents`, which shows names and not the Role column of `INBOX.md`,
so a focus chat (never a reviewer, see the `workflow:focus` skill) was sometimes asked for a
review. When the user's prompt is "focus mode", "talk mode", "conversation chat", `/focus` or
`/talk`, this hook sets the session title (Claude Code docs, hooks reference, UserPromptSubmit
decision control: `sessionTitle`) to `focus-<label>`, where the label is `chat_title`'s folder label
(`<repo>-<folder>` inside the `<repo>/main` layout), so `ListAgents` can show the role and the
repository. A chat already titled `focus-...` is left alone.

Fails open: any error prints nothing and exits 0.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chat_title import folder_label  # noqa: E402

TRIGGER = re.compile(r"^\s*(/focus|/talk|focus mode|talk mode|conversation chat)\b", re.IGNORECASE)
PREFIX = "focus-"


def title_for(prompt: str, cwd: str, current_title: str) -> str | None:
    """The title to set, or None when the prompt is not a focus start or the title already fits."""
    if not TRIGGER.match(prompt) or current_title.lower().startswith(PREFIX):
        return None
    return PREFIX + folder_label(cwd)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    title = title_for(
        str(payload.get("prompt") or ""),
        str(payload.get("cwd") or ""),
        str(payload.get("session_title") or ""),
    )
    if title:
        output = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "sessionTitle": title}}
        print(json.dumps(output))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken hook must never block the session
        pass
