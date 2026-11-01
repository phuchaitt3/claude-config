"""SessionStart and UserPromptSubmit hook: tell each chat the global review mode.

The user picks how pull requests are checked before an agent merges them, once for every project, in
`~/claude-config/settings/review.json` (`mode`, `since`, `why`). The modes and what each one asks are
in the `workflow:pr-review` skill, "Review modes"; this hook only announces the live value, so no
prose copy of the setting can drift (standard: standards/policy-single-source, checked 2026-11-01).

SessionStart always announces the mode. UserPromptSubmit announces it again only when the file says
something different from what this session was last told. A missing, broken or unknown setting
counts as `peer`, the strictest mode, and the line says so.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MODES = ("peer", "self-review", "self-diff", "ci-only")
SETTINGS_FILE = Path.home() / "claude-config" / "settings" / "review.json"
CACHE_DIR = Path.home() / ".claude" / "hook-cache" / "review_mode"


def read_mode(path: Path = SETTINGS_FILE) -> tuple[str, str]:
    """(mode, the line to show). Falls back to peer when the setting is missing or invalid."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        mode = str(data["mode"])
    except (OSError, ValueError, KeyError, TypeError):
        return "peer", f"Review mode: peer (fallback: {path.name} is missing or unreadable)."
    if mode not in MODES:
        return "peer", f"Review mode: peer (fallback: unknown mode {mode!r} in {path.name})."
    since = data.get("since") or "?"
    why = data.get("why") or "no reason given"
    return mode, f"Review mode: {mode} (since {since}; {why})."


def decide(event: str, told: str | None, mode: str, line: str) -> tuple[str | None, str]:
    """(what this session has now been told, text to add or '')."""
    if event == "SessionStart" or told != line:
        return line, (
            f"{line} Before merging a pull request, follow the `workflow:pr-review` skill, "
            f'"Review modes", for `{mode}`; hard limits and user-merge paths apply in every mode.'
        )
    return told, ""


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
    path = CACHE_DIR / f"{session}.txt"
    told = path.read_text(encoding="utf-8") if path.exists() else None
    mode, line = read_mode()
    told, text = decide(event, told, mode, line)
    if told is not None:
        path.write_text(told, encoding="utf-8")
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken hook must never block the session
        pass
