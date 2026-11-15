"""Check: point a chat that works on laptop temperature at the machine notes.

Runs before a tool call whose input mentions the thermal log, the thermal report, the processor
cap or the Lenovo power-mode tool. It adds one line, once per session, naming the machine notes
file (`personal-notes/main/machine/laptop-legion-y540.md`, found as a sibling of the project
folders from the chat's working directory, so no absolute path is stored here). Reminder only: it
never blocks. Users' decision, 2026-11-15: hook check, global scope.
"""

import json
import re
from pathlib import Path

EVENTS = {"PreToolUse"}
NOTES_REL = Path("personal-notes") / "main" / "machine" / "laptop-legion-y540.md"
PATTERN = re.compile(
    r"thermal\.jsonl|report --thermal|gpu_run\.py thermal|PROCTHROTTLEMAX|llt\.exe|"
    r"LenovoLegionToolkit|laptop-thermal-tiers|laptop-cpu-thermal-limit|CoreTempMappingObject",
    re.I,
)
MARKER_DIR = Path.home() / ".claude" / "hook-cache"


def _find_notes(cwd: str) -> Path | None:
    start = Path(cwd) if cwd else Path.cwd()
    for parent in [start, *start.parents]:
        candidate = parent / NOTES_REL
        if candidate.is_file():
            return candidate
    return None


def run(payload, marker_dir: Path = MARKER_DIR):
    text = json.dumps(payload.get("tool_input", {}), default=str)
    if not PATTERN.search(text) or "laptop-legion-y540" in text:
        return None
    notes = _find_notes(str(payload.get("cwd", "")))
    if notes is None:
        return None
    sid = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("session_id", "none")))
    marker = marker_dir / f"thermal-notes-{sid}"
    if marker.exists():
        return None
    try:
        marker_dir.mkdir(parents=True, exist_ok=True)
        marker.write_text("1", encoding="utf-8")
    except OSError:
        pass
    return (f"Laptop temperature work: the machine notes hold the thermal limits, test results, "
            f"current CPU cap and Lenovo mode, and the trigger for changing them: {notes}. Read "
            f"the thermal sections before changing a setting, and log a new test result or "
            f"setting change there in the same turn (the repo may be pushed to main).")
