"""Keep Windows from idle-sleeping while a background command runs (claude-config#7).

Three entry points, one file:

- PreToolUse (Bash|PowerShell), no argument: when the call has `run_in_background` and is not a
  recognised long-lived server, start a hidden, detached holder (`pythonw keep_awake.py hold ...`)
  and return nothing. The command is not changed: a rewritten command would be checked against the
  permission rules as rewritten (allow rules stop matching) and auto mode may deny it (Claude Code
  hooks docs, "PreToolUse decision control", `updatedInput`, read 2026-11-11).
- `hold`: the holder. It calls `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)`, then
  finds the tool's shell: the first process started after the holder that is a direct child of
  `claude.exe` and is either `bash.exe` whose command line holds the command's words (Bash tool) or
  `cmd.exe` launching `CLAUDE_CODE_SHELL_LAUNCHER_SCRIPT` (PowerShell tool, whose script travels in
  an environment variable). It waits for that process to exit (an event wait, no polling), then
  keeps the hold through the agent's next turn (grace, below) and exits, which releases the hold.
  Windows drops the hold when the holder dies, too (tested 2026-11-11, claude-config#6). No time
  estimate for the command itself. If no shell turns up within DISCOVER_S, it gives up.
- **Grace** (user's decision, 2026-11-11, after a laptop slept one second after a run ended and the
  agent's next step waited 5.5 hours): between a command's exit and the next command's own hold,
  the agent is reading the result, and an idle timer that ran out long ago sleeps the machine in
  that gap. So after its command exits the holder waits for the session's next turn to end: a turn
  start (UserPromptSubmit, which also fires for a task notification) after the exit, then a turn
  end (Stop) after that start. It also releases when claude.exe exits, or GRACE_CAP_S after the exit
  (a turn cut off by Esc or an API error may fire no Stop). It polls the turn marks every GRACE_POLL_S.
- `stop` (Stop): records the turn end for the session.
- `status` (UserPromptSubmit): records the turn start for the session, and adds `keep-awake: N holds (oldest 9 h: <command>)` to the chat's
  context when the set of holds changed since this session's last line, or while one is over
  LONG_HOLD_H hours old, so a forgotten hold is seen. Holds are machine-wide, so all are listed.

Skipped (no hold): `pnpm|npm|yarn [run] dev`, `next dev`, `--reload`, `--watch`, `serve` as a word,
`docker compose up` without `-d`. A `# keepawake: on` or `# keepawake: off` marker in the command
overrides. The power plan is never changed, and a closed lid still sleeps the machine.

Two background calls in one batch race for matching shells. Each holder claims its shell with an
exclusive file in `claims/`, so no two holders watch the same one and every shell is covered. Two
PowerShell calls cannot be told apart (no command text on their command lines), so their holders
may swap, which only swaps the command names in the status line. Windows only; elsewhere a no-op.

Fails open: any error prints nothing and exits 0. Holder decisions are logged in
`~/.claude/hook-cache/keep_awake/holder.log`.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

CACHE_DIR = Path.home() / ".claude" / "hook-cache" / "keep_awake"
HOLDS_DIR = CACHE_DIR / "holds"
CLAIMS_DIR = CACHE_DIR / "claims"
DISCOVER_S = 90.0  # other PreToolUse hooks may run up to 30 s before the tool's shell starts
POLL_S = 0.25
LONG_HOLD_H = 4.0
GRACE_CAP_S = 3600.0
GRACE_POLL_S = 5.0
LOG_MAX = 200_000

_MARKER = re.compile(r"#\s*keepawake:\s*(on|off)\b", re.IGNORECASE)
_SERVERS = [
    re.compile(r"\b(?:pnpm|npm|yarn|bun)\s+(?:run\s+)?dev\b"),
    re.compile(r"\bnext\s+dev\b"),
    re.compile(r"(?<![\w-])--reload\b"),
    re.compile(r"(?<![\w-])--watch\b"),
    re.compile(r"(?<![\w./-])serve(?![\w.-])"),
]
_COMPOSE_UP = re.compile(r"\bdocker[\s-]+compose\b[^;&|\n]*\bup\b([^;&|\n]*)")
_DETACH = re.compile(r"(?<![\w-])(?:-d|--detach|-\w*d\w*)(?![\w-])")
_WORD = re.compile(r"[A-Za-z0-9_]{4,}")
PS_LAUNCHER = "CLAUDE_CODE_SHELL_LAUNCHER_SCRIPT"


# --- deciding -------------------------------------------------------------------------------


def wants_hold(command: str) -> bool:
    """True when a background command should hold off idle sleep."""
    marker = _MARKER.findall(command)
    if marker:
        return marker[-1].lower() == "on"
    if any(p.search(command) for p in _SERVERS):
        return False
    for match in _COMPOSE_UP.finditer(command):
        if not _DETACH.search(match.group(1)):
            return False
    return True


def fingerprint(command: str, limit: int = 4) -> list[str]:
    """Distinct words of the command, longest first, used to recognise the Bash tool's shell."""
    words = sorted(set(_WORD.findall(command)), key=lambda w: (-len(w), w))
    return words[:limit]


def matches_shell(tool: str, name: str, cmdline: str, words: list[str]) -> bool:
    name = name.lower()
    if tool == "PowerShell":
        return name == "cmd.exe" and PS_LAUNCHER in cmdline
    if tool == "Bash":
        if name != "bash.exe" or PS_LAUNCHER in cmdline:
            return False
        # A command with no long word (`ls &`) falls back to the tool's snapshot preamble.
        return all(w in cmdline for w in words) if words else "shell-snapshots" in cmdline
    return False


def grace_over(exited: float, marks: dict, now: float, cap: float = GRACE_CAP_S) -> str | None:
    """Why a hold whose command exited at `exited` may end now, or None to keep holding.
    `marks` holds the session's last turn start (`prompt`) and turn end (`stop`) times."""
    prompt, stop = marks.get("prompt", 0.0), marks.get("stop", 0.0)
    if prompt > exited and stop > prompt:
        return "the next turn ended"
    if now - exited >= cap:
        return f"no turn end within {cap / 60:.0f} min"
    return None


def session_key(session: object) -> str:
    return re.sub(r"[^\w-]", "", str(session))[:64] or "unknown"


def marks_path(session: object) -> Path:
    return CACHE_DIR / f"turns-{session_key(session)}.json"


def read_marks(session: object) -> dict:
    try:
        data = json.loads(marks_path(session).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_mark(session: object, kind: str, when: float | None = None) -> None:
    marks = read_marks(session)
    marks[kind] = time.time() if when is None else when
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    marks_path(session).write_text(json.dumps(marks), encoding="utf-8")


def status_line(holds: list[dict], now: float) -> str:
    if not holds:
        return ""
    oldest = min(holds, key=lambda h: h.get("started", now))
    hours = (now - oldest.get("started", now)) / 3600
    age = f"{hours:.0f} h" if hours >= 1 else f"{hours * 60:.0f} min"
    command = " ".join(str(oldest.get("command", "")).split())
    if len(command) > 80:
        command = command[:77] + "..."
    noun = "hold" if len(holds) == 1 else "holds"
    grace = sum(1 for h in holds if h.get("exited"))
    after = f", {grace} past its command until the next turn ends" if grace else ""
    return (
        f"keep-awake: {len(holds)} {noun}{after} (oldest {age}: {command}). Each ends when its "
        "command exits and the next turn ends; stop a forgotten one with TaskStop."
    )


# --- Windows process helpers (ctypes) --------------------------------------------------------


def _win():
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260),
        ]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.SetThreadExecutionState.restype = wintypes.DWORD
    k32.SetThreadExecutionState.argtypes = [wintypes.DWORD]
    return ctypes, wintypes, k32, PROCESSENTRY32W


def processes() -> dict[int, tuple[int, str]]:
    """pid -> (parent pid, exe name) from a Toolhelp snapshot."""
    ctypes, _, k32, entry_t = _win()
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    out: dict[int, tuple[int, str]] = {}
    entry = entry_t()
    entry.dwSize = ctypes.sizeof(entry_t)
    try:
        ok = k32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            out[entry.th32ProcessID] = (entry.th32ParentProcessID, entry.szExeFile)
            ok = k32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        k32.CloseHandle(snap)
    return out


def command_line(pid: int) -> str:
    """The process's command line (NtQueryInformationProcess class 60, Windows 8.1+)."""
    ctypes, wintypes, k32, _ = _win()
    ntdll = ctypes.WinDLL("ntdll")
    handle = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return ""
    try:
        size = wintypes.ULONG(0)
        ntdll.NtQueryInformationProcess(handle, 60, None, 0, ctypes.byref(size))
        if not size.value:
            return ""
        buf = ctypes.create_string_buffer(size.value)
        if ntdll.NtQueryInformationProcess(handle, 60, buf, size, ctypes.byref(size)) != 0:
            return ""

        class UNICODE_STRING(ctypes.Structure):
            _fields_ = [("Length", wintypes.USHORT), ("MaximumLength", wintypes.USHORT),
                        ("Buffer", ctypes.c_void_p)]

        us = UNICODE_STRING.from_buffer(buf)
        return ctypes.wstring_at(us.Buffer, us.Length // 2) if us.Buffer else ""
    finally:
        k32.CloseHandle(handle)


def alive(pid: int) -> bool:
    ctypes, wintypes, k32, _ = _win()
    handle = k32.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    try:
        code = wintypes.DWORD()
        return bool(k32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
    finally:
        k32.CloseHandle(handle)


def claude_pid(procs: dict[int, tuple[int, str]], start: int) -> int | None:
    """The nearest ancestor named claude.exe (or node.exe for an npm install)."""
    pid, seen = start, set()
    while pid in procs and pid not in seen:
        seen.add(pid)
        parent, name = procs[pid]
        if name.lower() in ("claude.exe", "node.exe"):
            return pid
        pid = parent
    return None


# --- holder ----------------------------------------------------------------------------------


def log(message: str) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = CACHE_DIR / "holder.log"
        if path.exists() and path.stat().st_size > LOG_MAX:
            path.write_text("", encoding="utf-8")
        stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{stamp} pid={os.getpid()} {message}\n")
    except OSError:
        pass


def claim_shell(shell: int, holder: int, claims: Path, is_alive=None) -> bool:
    """Take `shell` for this holder, so two holders never watch the same shell.

    The claim is a file created exclusively. A claim left by a dead holder (a crash, or a reused
    PID) is removed and taken over. With distinct shells per holder, every background shell is
    watched, so a swap between two same-batch calls cannot end a hold early.
    """
    is_alive = is_alive or alive
    claims.mkdir(parents=True, exist_ok=True)
    path = claims / f"{shell}.claim"
    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                owner = int(path.read_text(encoding="utf-8").strip() or 0)
            except (OSError, ValueError):
                owner = 0
            if owner and is_alive(owner):
                return False
            path.unlink(missing_ok=True)
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(holder))
        return True
    return False


def find_shell(claude: int, tool: str, words: list[str], before: set[int]) -> int | None:
    deadline = time.monotonic() + DISCOVER_S
    checked: set[int] = set()
    while time.monotonic() < deadline:
        for pid, (parent, name) in processes().items():
            if parent != claude or pid in before or pid in checked:
                continue
            if not matches_shell(tool, name, command_line(pid), words):
                checked.add(pid)
                continue
            if claim_shell(pid, os.getpid(), CLAIMS_DIR):
                return pid
            # Another holder took it first; look again on the next pass, in case it lets go.
        time.sleep(POLL_S)
    return None


def hold(spec_path: str) -> int:
    k32 = _win()[2]
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    Path(spec_path).unlink(missing_ok=True)
    before = set(spec["before"])
    k32.SetThreadExecutionState(0x80000000 | 0x1)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    record = HOLDS_DIR / f"{os.getpid()}.json"
    shell: int | None = None
    try:
        shell = find_shell(spec["claude"], spec["tool"], spec["words"], before)
        if shell is None:
            log(f"no {spec['tool']} shell found in {DISCOVER_S:.0f} s; no hold: {spec['command'][:120]!r}")
            return 0
        HOLDS_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "holder": os.getpid(), "shell": shell, "tool": spec["tool"], "command": spec["command"],
            "cwd": spec.get("cwd", ""), "session": spec.get("session", ""), "started": time.time(),
        }
        record.write_text(json.dumps(data), encoding="utf-8")
        log(f"holding for {spec['tool']} shell {shell}: {spec['command'][:120]!r}")
        handle = k32.OpenProcess(0x00100000, False, shell)  # SYNCHRONIZE
        if handle:
            k32.WaitForSingleObject(handle, 0xFFFFFFFF)  # INFINITE
            k32.CloseHandle(handle)
        exited = time.time()
        record.write_text(json.dumps({**data, "exited": exited}), encoding="utf-8")
        log(f"shell {shell} exited; holding until the next turn ends")
        while True:
            if not alive(spec["claude"]):
                reason = "claude.exe exited"
                break
            reason = grace_over(exited, read_marks(spec.get("session", "")), time.time())
            if reason:
                break
            time.sleep(GRACE_POLL_S)
        log(f"released: shell {shell} exited, {reason}")
        return 0
    finally:
        k32.SetThreadExecutionState(0x80000000)
        record.unlink(missing_ok=True)
        if shell is not None:
            (CLAIMS_DIR / f"{shell}.claim").unlink(missing_ok=True)


def pythonw() -> str:
    exe = Path(sys.executable)
    candidate = exe.with_name("pythonw.exe")
    return str(candidate if candidate.is_file() else exe)


def start_holder(payload: dict) -> None:
    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command", ""))
    procs = processes()
    claude = claude_pid(procs, os.getppid())
    if claude is None:
        log("no claude.exe ancestor; no hold")
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    spec = CACHE_DIR / f"spec-{os.getpid()}-{time.time_ns()}.json"
    spec.write_text(json.dumps({
        "claude": claude, "tool": payload.get("tool_name"), "command": command,
        "words": fingerprint(command), "before": sorted(procs),
        "cwd": payload.get("cwd", ""), "session": payload.get("session_id", ""),
    }), encoding="utf-8")
    flags = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_PROCESS_GROUP | NO_WINDOW
    args = [pythonw(), str(Path(__file__).resolve()), "hold", str(spec)]
    io = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    try:
        subprocess.Popen(args, creationflags=flags | 0x01000000, close_fds=True, **io)  # BREAKAWAY
    except OSError:  # the job object refuses breakaway
        subprocess.Popen(args, creationflags=flags, close_fds=True, **io)


def pre_tool_use(payload: dict) -> None:
    if payload.get("tool_name") not in ("Bash", "PowerShell"):
        return
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict) or not tool_input.get("run_in_background"):
        return
    if wants_hold(str(tool_input.get("command", ""))):
        start_holder(payload)


# --- status ----------------------------------------------------------------------------------


def active_holds() -> list[dict]:
    holds = []
    for path in sorted(HOLDS_DIR.glob("*.json")) if HOLDS_DIR.is_dir() else []:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if alive(int(data.get("holder", 0))):
            holds.append(data)
        else:
            path.unlink(missing_ok=True)
    return holds


def status(payload: dict) -> None:
    write_mark(payload.get("session_id", ""), "prompt")
    holds = active_holds()
    now = time.time()
    session = session_key(payload.get("session_id", ""))
    seen_file = CACHE_DIR / f"seen-{session}.json"
    key = sorted(int(h["holder"]) for h in holds)
    try:
        previous = json.loads(seen_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        previous = []
    long_running = any(now - h.get("started", now) >= LONG_HOLD_H * 3600 for h in holds)
    if key == previous and not long_running:
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    seen_file.write_text(json.dumps(key), encoding="utf-8")
    line = status_line(holds, now) or "keep-awake: no holds."
    if not holds and not previous:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": line,
    }}))


def main(argv: list[str]) -> int:
    if sys.platform != "win32":
        return 0
    if len(argv) >= 2 and argv[0] == "hold":
        try:
            return hold(argv[1])
        except Exception as exc:  # the holder must never linger on an error
            log(f"holder error: {exc!r}")
            return 0
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    try:
        if argv[:1] == ["status"]:
            status(payload)
        elif argv[:1] == ["stop"]:
            write_mark(payload.get("session_id", ""), "stop")
        else:
            pre_tool_use(payload)
    except Exception as exc:  # never get in the way of a tool call
        log(f"hook error: {exc!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
