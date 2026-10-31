"""SessionEnd hook: remove this chat's row from the INBOX registry when the session ends.

`/clear` ends a session and starts a new one with a new ID, so the old row would otherwise sit in
the "Chats" table until its 2-hour lease expires. The row is matched by the first six characters of
the session ID (the short form `ListAgents` and the registry use).

Fails open: outside a handoff repository, or on any error, it changes nothing and exits 0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from skill_nudge import handoff_folder, main_checkout  # noqa: E402

def drop_rows(text: str, short_id: str) -> str:
    """The inbox text without table rows whose Session cell holds `short_id`."""
    kept = []
    for line in text.splitlines(keepends=True):
        cells = [c.strip(" `") for c in line.split("|")]
        if line.startswith("|") and len(cells) > 2 and cells[2] == short_id:
            continue
        kept.append(line)
    return "".join(kept)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    session_id = str(payload.get("session_id") or "")
    root = main_checkout(Path(payload.get("cwd") or "."))
    folder = handoff_folder(root) if root else None
    inbox = folder / "INBOX.md" if folder else None
    if len(session_id) < 6 or inbox is None or not inbox.is_file():
        return
    text = inbox.read_text(encoding="utf-8")
    updated = drop_rows(text, session_id[:6])
    if updated != text:
        inbox.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # fail open: a cleanup hook must never block ending a session
        pass
