"""Check: catch a decision record or design note that merges, or stays, with a stale status.

User's decision, 2026-11-27, after an ADR merged as "Proposed" and stayed so for 13 days although
the merge accepted it, and design notes in another project stayed "Proposed" after the work was
built. Rule: `workflow:adr`, rule 9. Reminder only; it never blocks.

- On `gh pr create` and `gh pr merge` (PreToolUse): reads the PR's diff (`git diff <base>...HEAD`
  before the PR exists, `gh pr diff` at merge) and names each Markdown file whose added lines set a
  status of Proposed or draft with no `Open until:` line in that file's patch.
- Once per repository per day (UserPromptSubmit): scans the tracked Markdown files for a Proposed or
  draft status with no `Open until:`, or with an `Open until:` date that has passed. Local reads
  only, no network.

A template line that lists choices (`Status: Proposed | Accepted`) is not a status.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shlex
import subprocess
from pathlib import Path

EVENTS = {"PreToolUse", "UserPromptSubmit"}
TOOLS = {"Bash", "PowerShell"}
CACHE = Path.home() / ".claude" / "hook-cache" / "status-sweep.json"
MAX_LISTED = 5

# "Status" in any case; the value as a status word ("Proposed", "draft" or "Draft"), so prose such
# as "Status: proposed in Chapter 5, not started" is not read as a record's status.
_STATUS = re.compile(r"\b(?i:status):[\s*]*(Proposed|[Dd]raft)\b(?![\s*]*\|)")
_OPEN_UNTIL = re.compile(r"Open until:[\s*]*(\d{4}-\d{2}-\d{2})?", re.I)
_GH_PR = re.compile(r"\bgh\s+pr\s+(create|merge)\b(.*)", re.I | re.S)
_RULE = "(workflow:adr, rule 9)"


def _git(args: list[str], cwd: str, timeout: float = 10) -> str | None:
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout if out.returncode == 0 else None


def flag_patch(patch: str) -> list[str]:
    """Markdown files in a unified diff that add a Proposed or draft status with no Open until."""
    flagged, name, text = [], None, []

    def close():
        added = [l[1:] for l in text if l.startswith("+") and not l.startswith("+++")]
        if name and name.lower().endswith(".md") and any(_STATUS.search(l) for l in added) \
                and not any(_OPEN_UNTIL.search(l) for l in text):
            flagged.append(name)

    for line in patch.splitlines():
        if line.startswith("diff --git "):
            close()
            name, text = line.rsplit(" b/", 1)[-1], []
        else:
            text.append(line)
    close()
    return flagged


def stale_in_file(text: str, today: dt.date) -> str | None:
    """Why a file's status is stale, or None."""
    if not any(_STATUS.search(l) for l in text.splitlines()):
        return None
    m = _OPEN_UNTIL.search(text)
    if not m:
        return "Proposed or draft with no Open until"
    if m.group(1):
        try:
            if dt.date.fromisoformat(m.group(1)) < today:
                return f"Open until {m.group(1)} has passed"
        except ValueError:
            return None
    return None


def merge_target(tokens: list[str]) -> list[str]:
    """`gh pr diff` arguments for the PR a `gh pr merge` names: its number, URL or branch, and -R."""
    target, repo, i = [], [], 0
    while i < len(tokens):
        t = tokens[i]
        if t in ("-R", "--repo") and i + 1 < len(tokens):
            repo, i = [t, tokens[i + 1]], i + 2
            continue
        if t.startswith("-"):
            # value-taking merge flags; their value is not the PR
            i += 2 if t in ("-b", "--body", "-t", "--subject", "-F", "--body-file", "-A",
                            "--author-email", "--match-head-commit") else 1
            continue
        if not target:
            target = [t.lstrip("#")]
        i += 1
    return target + repo


def _pr_reminder(command: str, cwd: str) -> str | None:
    m = _GH_PR.search(command)
    if not m:
        return None
    verb, rest = m.group(1).lower(), m.group(2).split("&&")[0].split(";")[0]
    if verb == "create":
        base = "origin/HEAD" if _git(["rev-parse", "--verify", "-q", "origin/HEAD"], cwd) else "origin/main"
        patch = _git(["diff", f"{base}...HEAD"], cwd)
    else:
        try:
            tokens = shlex.split(rest)
        except ValueError:
            tokens = rest.split()
        args = merge_target(tokens)
        try:
            out = subprocess.run(["gh", "pr", "diff", *args], cwd=cwd, capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=15)
            patch = out.stdout if out.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            patch = None
    files = flag_patch(patch or "")
    if not files:
        return None
    return (f"status-check: {', '.join(files)} would merge with status Proposed or draft and no "
            f"`Open until:` line. If merging accepts it, set Accepted in this PR; if it stays open on "
            f"purpose, add `**Open until:** <YYYY-MM-DD or #issue>` to its status line {_RULE}.")


def _sweep(cwd: str, today: dt.date) -> str | None:
    top = (_git(["rev-parse", "--show-toplevel"], cwd) or "").strip()
    if not top:
        return None
    try:
        seen = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        seen = {}
    if seen.get(top) == today.isoformat():
        return None
    seen[top] = today.isoformat()
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(seen), encoding="utf-8")
    except OSError:
        pass
    hits = []
    for rel in (_git(["ls-files", "*.md"], top) or "").splitlines():
        if any(part.startswith(".") for part in Path(rel).parts):
            continue
        try:
            why = stale_in_file((Path(top) / rel).read_text(encoding="utf-8", errors="replace"), today)
        except OSError:
            continue
        if why:
            hits.append(f"{rel} ({why})")
    if not hits:
        return None
    more = f" and {len(hits) - MAX_LISTED} more" if len(hits) > MAX_LISTED else ""
    return (f"status-check (daily): {len(hits)} status line(s) may be stale in this repository: "
            f"{'; '.join(hits[:MAX_LISTED])}{more}. Set the status the work reached, or add "
            f"`Open until:` if the item stays open on purpose {_RULE}. Mention it once; do not "
            f"interrupt the user's task for it.")


def run(payload):
    cwd = payload.get("cwd") or "."
    if payload.get("hook_event_name") == "UserPromptSubmit":
        return _sweep(cwd, dt.date.today())
    command = str((payload.get("tool_input") or {}).get("command", ""))
    return _pr_reminder(command, cwd) if "gh" in command else None
