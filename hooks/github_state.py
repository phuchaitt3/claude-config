"""UserPromptSubmit hook: tell the chat the current GitHub PR state, but only when it changed.

Agents only know GitHub's state from their last `gh` call, so a PR the user merged between
turns stays "open" in their memory. On each user message this hook reads the repo's open PRs,
the needs-you items and the PRs merged in the last 24 hours, and adds one line to the chat's
context when that differs from what it last told this session. Quiet turns add nothing.

Fails open: outside a GitHub repo, or if `gh` is missing or slow, it prints nothing and exits 0
(after a gh failure it says so once per session).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

CACHE_DIR = Path.home() / ".claude" / "hook-cache" / "github_state"
GH_TIMEOUT_S = 2.0  # two gh calls must fit in the hook's 5 s timeout


def run(args: list[str], cwd: str) -> str:
    result = subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=GH_TIMEOUT_S
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip()[:200])
    return result.stdout


def github_repo(cwd: str) -> str | None:
    try:
        url = run(["git", "remote", "get-url", "origin"], cwd).strip()
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
    return match.group(1) if match else None


def state_line(repo: str, cwd: str) -> str:
    open_prs = json.loads(
        run(["gh", "pr", "list", "-R", repo, "--state", "open",
             "--json", "number,title,labels,isDraft", "--limit", "30"], cwd)
    )
    since = (datetime.now(UTC) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    merged = json.loads(
        run(["gh", "pr", "list", "-R", repo, "--state", "merged", "--search", f"merged:>={since}",
             "--json", "number,mergedAt", "--limit", "20"], cwd)
    )

    def label_names(pr: dict) -> set[str]:
        return {label["name"] for label in pr.get("labels", [])}

    opened = ", ".join(
        f"#{pr['number']}{' (draft)' if pr.get('isDraft') else ''} {pr['title'][:50]}"
        for pr in sorted(open_prs, key=lambda p: p["number"])
    ) or "none"
    needs_you = ", ".join(
        f"#{pr['number']}" for pr in open_prs if "needs-you" in label_names(pr)
    ) or "none"
    recent = ", ".join(
        f"#{pr['number']} ({pr['mergedAt'][11:16]}Z)"
        for pr in sorted(merged, key=lambda p: p["mergedAt"], reverse=True)[:5]
    ) or "none"
    if len(merged) > 5:
        recent += f" and {len(merged) - 5} more"
    return f"open PRs: {opened} · needs-you PRs: {needs_you} · merged in last 24h: {recent}"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    cwd = payload.get("cwd") or "."
    session = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("session_id") or "nosession"))

    repo = github_repo(cwd)
    if repo is None:
        return
    try:
        line = state_line(repo, cwd)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        line = f"could not read GitHub state ({type(exc).__name__}); check with gh before reporting PR status"

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / f"{session}-{hashlib.sha1(repo.encode()).hexdigest()[:8]}.txt"
    if cache.exists() and cache.read_text(encoding="utf-8") == line:
        return
    cache.write_text(line, encoding="utf-8")

    now = datetime.now().astimezone().strftime("%H:%M")
    context = f"GitHub state of {repo} at {now} (changed since you last saw it): {line}"
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": context,
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken hook must never block the user's message
        pass
