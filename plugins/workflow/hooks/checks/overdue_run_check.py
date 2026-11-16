"""Check: tell the chat when a background command has run far past its estimate.

A background command that hangs never exits, so the harness never notifies the chat. keep_awake's
holder records every running background shell command (servers and `# keepawake: off` commands get
no record, so they are skipped); this check reads those records. When one of this chat's commands
has run longer than OVERDUE_FACTOR x its `# estimate:` tag (DEFAULT_LIMIT_MIN when it has none), it
adds one line, once per command. Reminder only: it never blocks (claude-config issue #18).
"""

import json
import re
import sys
import time
from pathlib import Path

EVENTS = {"UserPromptSubmit", "PreToolUse"}
OVERDUE_FACTOR = 2.0
DEFAULT_LIMIT_MIN = 20.0
MARKER_DIR = Path.home() / ".claude" / "hook-cache"


def _hooks_dir() -> str:
    return str(Path(__file__).resolve().parent.parent)


def _limit_min(command: str) -> tuple[float, float | None]:
    sys.path.insert(0, _hooks_dir())
    import run_estimate

    estimate = run_estimate.parse_estimate(command)
    if estimate is None:
        return DEFAULT_LIMIT_MIN, None
    return estimate * OVERDUE_FACTOR, estimate


def run(payload, holds=None, now=None, marker_dir: Path = MARKER_DIR):
    if holds is None:
        sys.path.insert(0, _hooks_dir())
        import keep_awake

        holds = keep_awake.active_holds()
    now = time.time() if now is None else now
    session = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("session_id", "")))
    lines = []
    for h in holds:
        if h.get("exited") or not h.get("shell") or h.get("tool") not in ("Bash", "PowerShell"):
            continue
        if re.sub(r"[^A-Za-z0-9_-]", "", str(h.get("session", ""))) != session:
            continue
        command = str(h.get("command", ""))
        limit, estimate = _limit_min(command)
        age_min = (now - float(h.get("started", now))) / 60
        if age_min < limit:
            continue
        marker = marker_dir / f"overdue-{session}-{h.get('holder')}"
        if marker.exists():
            continue
        try:
            marker_dir.mkdir(parents=True, exist_ok=True)
            marker.write_text("1", encoding="utf-8")
        except OSError:
            pass
        short = " ".join(command.split())[:80]
        basis = f"estimate {estimate:g} min" if estimate is not None else f"no estimate, {DEFAULT_LIMIT_MIN:g} min limit"
        lines.append(f"overdue background command: {short!r} has run {age_min:.0f} min ({basis}). "
                     "Check it; stop it with TaskStop if it is stuck.")
    return "\n".join(lines) or None
