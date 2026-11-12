"""SessionStart hook: tell the chat when other Claude chats are running on this machine.

The trigger used to be "this repository has a handoff folder", a proxy that missed a repository
whose folder only CLAUDE.md names, and every repository with no handoff folder at all (a chat there
could not see that another chat already held its task). The real condition is whether another chat
is alive, and `~/.claude/sessions` says so on every project: one JSON file per session with its pid,
session ID and working folder. A session counts as live when its process runs (the check
`claim_sweep` uses). The hook lists the other live chats and tells this one to load
`workflow:multi-chat`, run `ListAgents` and look at the recent commits of the repository it will
edit before starting. With no other chat running it prints nothing.

Limits: it sees only this machine (`ListAgents` has the same limit), and a recycled process ID can
count a dead chat as live, which costs one unneeded reminder. Fails open: any error prints nothing
and exits 0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from claim_sweep import pid_running

SESSIONS = Path.home() / ".claude" / "sessions"
MAX_LISTED = 6


def other_live_sessions(own_id: str, sessions: Path = SESSIONS) -> list[tuple[str, str]]:
    """(session ID prefix, working folder) of every live session except `own_id`, oldest first."""
    found: list[tuple[int, str, str]] = []
    for file in sessions.glob("*.json"):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            session_id = str(data["sessionId"])
            if session_id == own_id or not pid_running(int(data["pid"])):
                continue
            found.append((int(data.get("startedAt") or 0), session_id[:6], str(data.get("cwd") or "?")))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return [(prefix, cwd) for _, prefix, cwd in sorted(found)]


def message(peers: list[tuple[str, str]]) -> str:
    listed = "; ".join(f"{prefix} in {cwd}" for prefix, cwd in peers[:MAX_LISTED])
    more = f" (and {len(peers) - MAX_LISTED} more)" if len(peers) > MAX_LISTED else ""
    return (
        f"{len(peers)} other Claude chat(s) are running on this machine: {listed}{more}. Before any "
        "edit, load the `workflow:multi-chat` skill and follow its \"At the start of a chat\" "
        "steps: run `ListAgents`, and check the recent commits (`git log --since=1.day`), open "
        "claims and worktrees of every repository the task will change, including another "
        "repository when the task was handed over from here. A commit or claim for the same task "
        "means another chat holds it: stop and ask the user."
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    peers = other_live_sessions(str(payload.get("session_id") or ""))
    if not peers:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": message(peers),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken hook must never block the session
        pass
