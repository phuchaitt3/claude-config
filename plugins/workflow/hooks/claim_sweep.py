"""SessionStart hook: release `claimed` issues whose claimant chat has been closed.

A chat that is closed cannot release its own claims, so a `claimed` label could stay on an issue
for good and the next chat skipped it. This hook does it from outside, at most once an hour per
repository, in a detached worker. Acts only where the main checkout has a handoff folder.

A claim comment reads `claimed by <session ID> (uuid <first 8 characters of the session UUID>,
<machine>) ...`. For each issue with the label, the latest claim comment decides. The claim is
released (label removed, one comment) only when every check passes:

- uuid claim: it names this machine, is over 2 hours old, no file in `~/.claude/sessions` has a
  sessionId starting with the prefix and a running process, and no open PR names the issue;
- older claim with no uuid: it is over 24 hours old and no open PR names the issue;
- a claim that names another machine is never released here (its Last seen row covers it).

Every decision is logged; the next session start shows one line when claims were released.
`python claim_sweep.py sweep <main checkout> --dry-run` prints the decisions and changes nothing.
"""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _gitcmd import CACHE_ROOT, main_checkout_of, opted_in, repo_key, spawn_detached

CACHE = CACHE_ROOT / "claim_sweep"
SESSIONS = Path.home() / ".claude" / "sessions"
INTERVAL_S = 60 * 60
MIN_AGE = timedelta(hours=2)
MIN_AGE_NO_UUID = timedelta(hours=24)

CLAIM = re.compile(r"claimed by\b", re.IGNORECASE)
UUID_PART = re.compile(r"\(uuid ([0-9a-f]{8}),\s*([^)\s]+)\)", re.IGNORECASE)


def parse_time(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def latest_claim(comments: list[dict]) -> dict | None:
    claims = [c for c in comments if CLAIM.search(c.get("body", "")[:80])]
    return max(claims, key=lambda c: c["createdAt"]) if claims else None


def pid_running(pid: int) -> bool:
    if os.name == "nt":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def live_prefixes(sessions: Path = SESSIONS) -> set[str]:
    """First 8 characters of the sessionId of every session whose process is running."""
    found: set[str] = set()
    for file in sessions.glob("*.json"):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            if pid_running(int(data["pid"])):
                found.add(str(data["sessionId"])[:8].lower())
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return found


def names_issue(number: int, pr: dict) -> bool:
    text = f"{pr.get('title', '')}\n{pr.get('body', '')}"
    if re.search(rf"#{number}\b", text):
        return True
    return bool(re.search(rf"(^|[/-]){number}([-/]|$)", pr.get("headRefName", "")))


def decide(
    number: int, comments: list[dict], open_prs: list[dict], live: set[str], host: str,
    now: datetime,
) -> tuple[bool, str, str | None]:
    """(release?, reason, prefix of the claimant's session UUID if the claim names one)."""
    claim = latest_claim(comments)
    if claim is None:
        return False, "no claim comment", None
    age = now - parse_time(claim["createdAt"])
    match = UUID_PART.search(claim["body"])
    prefix = match.group(1).lower() if match else None
    if any(names_issue(number, pr) for pr in open_prs):
        return False, "an open PR names it", prefix
    if match is None:
        if age < MIN_AGE_NO_UUID:
            return False, "claim has no uuid and is under 24 hours old", None
        return True, "claim has no uuid, is over 24 hours old, and no open PR names it", None
    if match.group(2).lower() != host.lower():
        return False, f"claim is from machine {match.group(2)}", prefix
    if age < MIN_AGE:
        return False, "claim is under 2 hours old", prefix
    if prefix in live:
        return False, f"session {prefix} is running", prefix
    return True, f"session {prefix} is gone and no open PR names it", prefix


def gh_json(main: Path, *args: str) -> list[dict]:
    out = subprocess.run(
        ["gh", *args], cwd=str(main), capture_output=True, text=True, encoding="utf-8",
        timeout=60, check=True,
    ).stdout
    return json.loads(out)


def sweep(main: Path, dry_run: bool, now: datetime | None = None) -> list[str]:
    """Release the claims `decide` clears; return one line per decision."""
    now = now or datetime.now(timezone.utc)
    host = os.environ.get("COMPUTERNAME") or platform.node()
    issues = gh_json(main, "issue", "list", "--label", "claimed", "--state", "open", "--limit",
                     "100", "--json", "number,comments")
    if not issues:
        return []
    open_prs = gh_json(main, "pr", "list", "--state", "open", "--limit", "100", "--json",
                       "number,title,body,headRefName")
    live = live_prefixes()
    lines: list[str] = []
    for issue in issues:
        number = issue["number"]
        release, reason, prefix = decide(number, issue["comments"], open_prs, live, host, now)
        if release and not dry_run:
            who = f"session {prefix}" if prefix else "the chat that claimed it"
            try:
                subprocess.run(
                    ["gh", "issue", "edit", str(number), "--remove-label", "claimed"],
                    cwd=str(main), capture_output=True, timeout=60, check=True,
                )
                subprocess.run(
                    ["gh", "issue", "comment", str(number), "--body",
                     f"claim released by the claim_sweep hook: {who} is gone ({reason}). "
                     "Any chat may claim this issue."],
                    cwd=str(main), capture_output=True, timeout=60, check=True,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                release, reason = False, f"could not release: {exc}"
        lines.append(f"{'release' if release else 'keep'} #{number} {reason}")
    return lines


def log_path(main: Path) -> Path:
    return CACHE / f"{repo_key(main)}.log"


def run_sweep(main: Path) -> None:
    lines = sweep(main, dry_run=False)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path = log_path(main)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as log:
        log.writelines(f"{stamp} {line}\n" for line in lines)
    released = sum(line.startswith("release ") for line in lines)
    if released:
        state = CACHE / f"{repo_key(main)}.pending"
        state.write_text(str(released + _pending(state)), encoding="utf-8")


def _pending(state: Path) -> int:
    try:
        return int(state.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0


def on_session_start(payload: dict, now: float) -> str | None:
    main = main_checkout_of(str(payload.get("cwd") or "."))
    if main is None or not opted_in(main):
        return None
    stamp = CACHE / f"{repo_key(main)}.stamp"
    try:
        due = now - stamp.stat().st_mtime >= INTERVAL_S
    except OSError:
        due = True
    if due:
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.touch()
        spawn_detached([str(Path(__file__).resolve()), "sweep", str(main)])
    state = CACHE / f"{repo_key(main)}.pending"
    released = _pending(state)
    if not released:
        return None
    state.unlink(missing_ok=True)
    return (f"claim_sweep released {released} claim(s) whose chat had been closed "
            f"(log: {log_path(main)}).")


def main() -> int:
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "sweep":
        main_dir, dry_run = Path(args[1]), "--dry-run" in args[2:]
        if dry_run:
            print("\n".join(sweep(main_dir, dry_run=True)))
        else:
            run_sweep(main_dir)
        return 0
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if isinstance(payload, dict):
        note = on_session_start(payload, time.time())
        if note:
            json.dump({"hookSpecificOutput": {
                "hookEventName": "SessionStart", "additionalContext": note,
            }}, sys.stdout)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # a broken hook must never get in the way of a session
        if sys.argv[1:2] == ["sweep"] and "--dry-run" in sys.argv:
            raise
        sys.exit(0)
