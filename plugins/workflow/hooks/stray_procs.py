"""SessionStart / UserPromptSubmit hook: stop orphaned processes left behind by a shell call.

A shell tool call that times out or is stopped kills the shell but not its children on Windows, so a
`find`, `grep` or `rg` can keep running for hours with no parent (standard:
findings/agent-process-and-resource-control, checked 2026-11-12). This hook looks at most once every
ten minutes. It ends a process from a short list of search tools when it is older than 15 minutes
and its parent no longer exists, logs the kill to `~/.claude/stray-procs.log`, and tells the chat in
one line. A search tool whose parent is alive is only reported once it has run over an hour, because
a person may be waiting for it. Silent otherwise, on other platforms, and on any error: a broken
hook must never block a session.

The same timeout leaves `python -m pytest` and `node` test runs behind (the shell dies, its children
do not). A wider scan is risky, because a deliberate background job also looks like "python with
no visible parent", so it is narrow and two-tier:

- Ended (like a search tool): a test runner (the command line names pytest, py.test, unittest, jest,
  vitest or mocha, on python, py or node) whose parent is gone and that has run over 30 minutes. A
  foreground shell call is capped at 10 minutes and a background one keeps its shell alive, so a
  runner with no parent and a half-hour age is a leftover. It is ended with its child processes.
  A process whose parent pid now belongs to a younger process (the pid was reused) counts as
  parentless.
- Never touched: anything whose command line names `gpu_run` or `keepawake` (deliberate, guarded
  jobs), the process holding the GPU or RAM lock of `scripts/gpu_run.py` and its direct children.
- Only reported, once per process: any other python or node process with no parent and over 2
  hours, unless it looks like an editor, language server, MCP server, notebook or web server.
  Nothing else is ever ended; the real fix (a Job Object that kills the whole tree when the shell
  call ends) belongs in the Claude Code Bash tool, so this is the register's backstop
  (standard: findings/agent-process-and-resource-control, checked 2026-11-12).

Every kill is appended to `~/.claude/stray-procs.log` with the command line and age.
"""

from __future__ import annotations

import json
import re
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
RUNNER_ORPHAN_AFTER_S = 1800  # a foreground shell call lasts 10 minutes at most
UNKNOWN_ORPHAN_AFTER_S = 7200
RUNNER_HOSTS = {"python.exe", "py.exe", "pytest.exe", "node.exe"}
REPORT_HOSTS = {"python.exe", "pythonw.exe", "node.exe"}
_RUNNER = re.compile(r"(?<![\w.-])(pytest|py\.test|unittest|jest|vitest|mocha)(?![\w-])", re.IGNORECASE)
_GUARDED = ("gpu_run", "keepawake", "keep_awake")  # deliberate, lock-guarded or hold-off-sleep jobs
_LONG_LIVED = (  # editors, language servers, notebooks, web servers: orphaned by design, never reported
    "vscode", "pylance", "pyright", "language-server", "languageserver", "tsserver", "mcp", "jupyter",
    "ipykernel", "ollama", "uvicorn", "gunicorn", "http.server", "serve", "--reload", "--watch",
    "@anthropic", "claude-code", "claude.exe", "electron",
)

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


def _started(p: dict) -> float | None:
    try:
        return datetime.fromisoformat(p["Started"]).timestamp() if p.get("Started") else None
    except ValueError:
        return None


def _parentless(p: dict, by_pid: dict[int, dict]) -> bool:
    """True when the parent pid is gone, or now belongs to a process younger than this one (reuse)."""
    parent = by_pid.get(p["ParentProcessId"])
    if parent is None:
        return True
    born, parent_born = _started(p), _started(parent)
    return born is not None and parent_born is not None and parent_born > born


def classify_runners(
    procs: list[dict], now: float, protected: set[int] | frozenset[int] = frozenset()
) -> tuple[list[dict], list[dict]]:
    """(test runners to end, other parentless python/node processes to report). `protected` holds the
    pids of lock holders: neither they nor their direct children are ever listed."""
    by_pid = {p["ProcessId"]: p for p in procs}
    kill_list, report_list = [], []
    for p in procs:
        name = str(p.get("Name", "")).lower()
        born = _started(p)
        if name not in RUNNER_HOSTS | REPORT_HOSTS or born is None:
            continue
        if p["ProcessId"] in protected or p["ParentProcessId"] in protected or not _parentless(p, by_pid):
            continue
        command = str(p.get("CommandLine") or "")
        low = command.lower()
        if any(g in low for g in _GUARDED):
            continue
        age = now - born
        if name in RUNNER_HOSTS and _RUNNER.search(command) and age >= RUNNER_ORPHAN_AFTER_S:
            kill_list.append({**p, "age_s": age})
        elif age >= UNKNOWN_ORPHAN_AFTER_S and not any(w in low for w in _LONG_LIVED):
            report_list.append({**p, "age_s": age})
    return kill_list, report_list


def lock_holders() -> set[int]:
    """Pids that hold a gpu_run lock (gpu, ram) now; empty when the script is missing."""
    sys.path.insert(0, str(Path.home() / "claude-config" / "scripts"))
    pids: set[int] = set()
    try:
        import gpu_run

        for resource in getattr(gpu_run, "RESOURCES", {"gpu": ""}):
            lock = gpu_run.Lock(resource) if resource != "gpu" else gpu_run.Lock()
            if lock.is_held():
                pid = lock.holder().get("pid")
                if isinstance(pid, int):
                    pids.add(pid)
    except Exception:
        pass
    return pids


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


def kill(pid: int, tree: bool = False) -> bool:
    cmd = ["taskkill", "/F", "/T", "/PID", str(pid)] if tree else ["taskkill", "/F", "/PID", str(pid)]
    return subprocess.run(cmd, capture_output=True, timeout=10, check=False).returncode == 0


def log_kill(p: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as log:
        log.write(f"{datetime.now(timezone.utc).isoformat()} killed {describe(p)}\n")


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
    procs = list_processes()
    alive = {p["ProcessId"] for p in procs}
    reported = [pid for pid in state.get("reported", []) if pid in alive]
    CACHE.write_text(json.dumps({"checked": now, "reported": reported}), encoding="utf-8")
    orphans, long_runners = classify(procs, now)
    stale_runs, unknown = classify_runners(procs, now, lock_holders())
    lines = []
    for p in orphans:
        if kill(p["ProcessId"]):
            lines.append(f"ended orphaned {describe(p)}")
            log_kill(p)
    for p in stale_runs:
        if kill(p["ProcessId"], tree=True):
            lines.append(f"ended orphaned test run {describe(p)}")
            log_kill(p)
    lines += [f"still running with a live parent: {describe(p)}" for p in long_runners]
    new = [p for p in unknown if p["ProcessId"] not in reported]
    lines += [f"no parent, not ended: {describe(p)}" for p in new[:3]]
    if len(new) > 3:
        lines.append(f"{len(new) - 3} more like it")
    if new:
        CACHE.write_text(
            json.dumps({"checked": now, "reported": reported + [p["ProcessId"] for p in new]}), encoding="utf-8"
        )
    if lines:
        text = "stray processes (they slow the machine): " + "; ".join(lines) + "."
        if orphans or long_runners:
            text += " Do not start a whole-drive search; use Glob/Grep or a scoped path."
        if new:
            text += " The ones marked not ended were left alone: ask the user before ending any."
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": text}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
