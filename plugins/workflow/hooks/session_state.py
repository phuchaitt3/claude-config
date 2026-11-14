"""UserPromptSubmit hook: keep the chat in sync with which Claude sessions run on this machine.

The SessionStart notice names the other chats only once, so a session started later (an overnight
background run, a new panel chat) stays unknown, and an agent that answers from an earlier listing
undercounts (2026-11-15: an agent said one overnight run was going while two were). Like
`github_state`, this hook reads the live list on each user message, from `claude agents --json`,
and adds a line only when it differs from what it last told this session, so quiet turns cost
nothing. The line is a reading at message time; a statement later in the turn still re-checks
(working rules, "Status comes from gh", live state).

Fails open: if no claude binary is found or the listing is slow or malformed, it prints nothing.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

CACHE_DIR = Path.home() / ".claude" / "hook-cache" / "session_state"
TIMEOUT_S = 3.0


def claude_binary() -> str | None:
    """The extension's bundled claude.exe (newest version folder), else `claude` on PATH."""
    found = sorted(
        Path.home().glob(".vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude*"),
        key=lambda p: p.parent.parent.parent.name,
    )
    found = [p for p in found if p.name in ("claude", "claude.exe")]
    if found:
        return str(found[-1])
    return shutil.which("claude")


def read_sessions(binary: str) -> list[dict]:
    result = subprocess.run(
        [binary, "agents", "--json"], capture_output=True, text=True, encoding="utf-8",
        timeout=TIMEOUT_S,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip()[:200])
    data = json.loads(result.stdout)
    if not isinstance(data, list):
        raise ValueError("agents --json did not return a list")
    return data


def describe(sessions: list[dict], own_session: str) -> str:
    """One line: background sessions by name with status and start time, then interactive chats."""
    def started(s: dict) -> str:
        try:
            return datetime.fromtimestamp(s["startedAt"] / 1000).strftime("%H:%M")
        except (KeyError, TypeError, ValueError, OSError):
            return "?"

    background = sorted(
        (s for s in sessions if s.get("kind") == "background"), key=lambda s: s.get("startedAt", 0)
    )
    interactive = [s for s in sessions if s.get("kind") != "background"]
    bg = ", ".join(
        f"{s.get('name') or s.get('id') or '?'} ({s.get('status', '?')}, since {started(s)})"
        for s in background
    ) or "none"
    chats = ", ".join(
        f"{s.get('name') or '?'}{' (you)' if s.get('sessionId') == own_session else ''}"
        f" ({s.get('status', '?')})"
        for s in interactive
    ) or "none"
    return f"background sessions: {bg} · interactive chats: {chats}"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    own = str(payload.get("session_id") or "")
    session = re.sub(r"[^A-Za-z0-9_-]", "", own or "nosession")

    binary = claude_binary()
    if binary is None:
        return
    try:
        line = describe(read_sessions(binary), own)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired):
        return

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / f"{session}.txt"
    try:
        if cache.read_text(encoding="utf-8") == line:
            return
    except OSError:
        pass
    cache.write_text(line, encoding="utf-8")

    now = datetime.now().astimezone().strftime("%H:%M")
    context = (
        f"Claude sessions on this machine at {now} (changed since you last saw it): {line}. "
        "Count or name running chats and overnight runs from this line or a fresh "
        "`claude agents --json`, never from an earlier listing."
    )
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": context,
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken hook must never block the user's message
        pass
