"""SessionStart / UserPromptSubmit hook: stop orphaned search processes left behind by a shell call.

A shell tool call that times out or is stopped kills the shell but not its children on Windows, so a
`find`, `grep` or `rg` can keep running for hours with no parent (standard:
findings/agent-process-and-resource-control, checked 2026-11-12). This hook looks at most once every
ten minutes. It ends a process from a short list of search tools when it is older than 15 minutes
and its parent no longer exists, logs the kill to `~/.claude/stray-procs.log`, and tells the chat in
one line. A search tool whose parent is alive is only reported once it has run over an hour, because
a person may be waiting for it. Silent otherwise, on other platforms, and on any error: a broken
hook must never block a session.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CACHE = Path.home() / ".claude" / "hook-cache" / "stray_procs.json"
LOG = Path.home() / ".claude" / "stray-procs.log"
CHECK_EVERY_S = 600
ORPHAN_AFTER_S = 900
REPORT_AFTER_S = 3600
NAMES = {"find.exe", "grep.exe", "egrep.exe", "fgrep.exe", "rg.exe", "fd.exe", "yes.exe"}

_QUERY = (
    "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,"
    "@{n='Started';e={if($_.CreationDate){$_.CreationDate.ToUniversalTime().ToString('o')}}},"
    "CommandLine | ConvertTo-Json -Compress"
)


def classify(procs: list[dict], now: float) -> tuple[list[dict], list[dict]]:
    """(orphans to end, live-parent long runners to report) from a process list."""
    alive = {p["ProcessId"] for p in procs}
    orphans, long_runners = [], []
    for p in procs:
        if str(p.get("Name", "")).lower() not in NAMES or not p.get("Started"):
            continue
        age = now - datetime.fromisoformat(p["Started"]).timestamp()
        if p["ParentProcessId"] not in alive and age >= ORPHAN_AFTER_S:
            orphans.append({**p, "age_s": age})
        elif p["ParentProcessId"] in alive and age >= REPORT_AFTER_S:
            long_runners.append({**p, "age_s": age})
    return orphans, long_runners


def describe(p: dict) -> str:
    command = str(p.get("CommandLine") or p.get("Name"))
    return f"{p['Name']} {p['ProcessId']} ({p['age_s'] / 3600:.1f} h): {command[:90]}"


def list_processes() -> list[dict]:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", _QUERY],
        capture_output=True, text=True, encoding="utf-8", timeout=20, check=False,
    )
    data = json.loads(result.stdout or "[]")
    return data if isinstance(data, list) else [data]


def kill(pid: int) -> bool:
    return subprocess.run(
        ["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=10, check=False
    ).returncode == 0


def main() -> None:
    if sys.platform != "win32":
        return
    try:
        state = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    now = time.time()
    if now - state.get("checked", 0) < CHECK_EVERY_S:
        return
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"checked": now}), encoding="utf-8")
    orphans, long_runners = classify(list_processes(), now)
    lines = []
    for p in orphans:
        if kill(p["ProcessId"]):
            lines.append(f"ended orphaned {describe(p)}")
            with LOG.open("a", encoding="utf-8") as log:
                log.write(f"{datetime.now(timezone.utc).isoformat()} killed {describe(p)}\n")
    lines += [f"still running with a live parent: {describe(p)}" for p in long_runners]
    if lines:
        text = (
            "stray search processes (they slow the machine): " + "; ".join(lines)
            + ". Do not start a whole-drive search; use Glob/Grep or a scoped path."
        )
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": text}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
