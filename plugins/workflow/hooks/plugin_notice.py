"""SessionStart and UserPromptSubmit hook: tell a running chat once about a critical plugin update.

A chat keeps the plugin text it loaded until the user types `/reload-plugins` (or opens a new
session). Most updates can wait for that. A critical one (a wrong hard limit, merge or push gate,
registry or messaging rule) must not, so `critical.json` next to the hooks names the latest one and
when it was published. A chat that started before that time is told once, with the reason, to have
the user type `/reload-plugins`; the chat itself cannot run that command.

SessionStart records when the session began. UserPromptSubmit compares that with `critical.json`.
A session the hook has not seen start (open before the hook was installed) counts as starting at its
first prompt, so only updates published after that are announced. "Told" is stored per session and
per update, so a later critical update is announced again.

Fails open: a missing or broken file, or any error, prints nothing and exits 0.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

CACHE_DIR = Path.home() / ".claude" / "hook-cache" / "plugin_notice"
CRITICAL_FILE = Path(__file__).resolve().parent.parent / "critical.json"


def read_critical(path: Path = CRITICAL_FILE) -> tuple[str, datetime, str] | None:
    """(version, published at, reason) from critical.json, or None if absent or malformed."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        published = datetime.fromisoformat(data["since"])
        if published.tzinfo is None:
            return None
        return str(data["version"]), published, str(data.get("why") or "no reason given")
    except (OSError, ValueError, KeyError, TypeError):
        return None


def load_state(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def notice(version: str, why: str) -> str:
    return (
        f"Critical update to the workflow plugin ({version}): {why}. This chat still runs the older "
        "text. Tell the user in one line to type `/reload-plugins` in this window (you cannot run it "
        "yourself); until then, do not rely on the rules this chat loaded."
    )


def decide(event: str, state: dict, critical: tuple[str, datetime, str] | None, now: datetime) -> tuple[dict, str]:
    """(new state, text to add to the context or '')."""
    state = dict(state)
    if event == "SessionStart" or "start" not in state:
        state["start"] = now.isoformat()
    if event != "UserPromptSubmit" or critical is None:
        return state, ""
    version, published, why = critical
    started = datetime.fromisoformat(state["start"])
    if published <= started or state.get("told") == published.isoformat():
        return state, ""
    state["told"] = published.isoformat()
    return state, notice(version, why)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    event = str(payload.get("hook_event_name") or "")
    if event not in ("SessionStart", "UserPromptSubmit"):
        return
    session = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("session_id") or "nosession"))
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{session}.json"
    state, text = decide(event, load_state(path), read_critical(), datetime.now().astimezone())
    path.write_text(json.dumps(state), encoding="utf-8")
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken hook must never block the session
        pass
