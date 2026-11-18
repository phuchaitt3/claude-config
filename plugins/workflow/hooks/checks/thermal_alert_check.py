"""Check: tell the chat when `gpu_run.py` warned about, or stopped, a hot GPU job.

The wrapper around a GPU job (`gpu_run.py run`) reads the GPU temperature every 15 s against the
card's own limits and writes `thermal_warn` or `thermal_stop` to `~/.gpu-guard/events.jsonl`
(user's decision, 2026-11-18). A chat is not watching that file, so this check reads it before each
prompt and tool call and adds one line per new event, naming what to do: a warn is a reason to look at
the cooling check and the cap (`laptop_health.py due --kind cap-bench` now says so); a stop means the
job was ended and must be restarted deliberately. Reminder only: it never blocks.
"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

EVENTS = {"UserPromptSubmit", "PreToolUse"}
MAX_AGE_MIN = 120
MARKER_DIR = Path.home() / ".claude" / "hook-cache"


def _events_path() -> Path:
    return Path(os.environ.get("GPU_GUARD_DIR") or Path.home() / ".gpu-guard") / "events.jsonl"


def _recent(path: Path, now: datetime) -> list[dict]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-400:]
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            e = json.loads(line)
            if e.get("event") in ("thermal_warn", "thermal_stop") and now - datetime.fromisoformat(e["ts"]) <= timedelta(minutes=MAX_AGE_MIN):
                out.append(e)
        except (ValueError, KeyError, TypeError):
            continue
    return out


def run(payload, marker_dir: Path = MARKER_DIR, path: Path | None = None, now: datetime | None = None):
    now = now or datetime.now().astimezone()
    found = _recent(path or _events_path(), now)
    if not found:
        return None
    sid = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("session_id", "none")))
    marker = marker_dir / f"thermal-alert-{sid}"
    try:
        seen = marker.read_text(encoding="utf-8").strip()
    except OSError:
        seen = ""
    new = [e for e in found if e["ts"] > seen]
    if not new:
        return None
    try:
        marker_dir.mkdir(parents=True, exist_ok=True)
        marker.write_text(new[-1]["ts"], encoding="utf-8")
    except OSError:
        pass
    last = new[-1]
    what = ("STOPPED a GPU job that stayed near the card's slowdown temperature" if last["event"] == "thermal_stop"
            else "warned that a GPU job ran hot or hit thermal slowdown")
    return (f"thermal-alert: gpu_run {what} ({last.get('temp_c')} C at {last['ts'][:19]}, job: {last.get('purpose')}). "
            f"Tell the user, check the cooling (`laptop_health.py report`), and do not restart a stopped job unchanged; "
            f"`laptop_health.py due --kind cap-bench` now says the cap benchmark is due.")
