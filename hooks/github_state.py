"""UserPromptSubmit hook: keep the chat in sync with GitHub's merge state.

Agents only know GitHub's state from their last `gh` call, so a PR the user merged between turns
stays "open" in their memory. On each user message this hook reads the repo's open PRs, the
needs-you items, the PRs merged in the last 24 hours and the PR of the branch checked out in the
chat's folder. It adds a line to the chat's context only when that differs from what it last told
this session, so quiet turns cost nothing. Two things make it a sync mechanism, not just a report:

- a PR merged since the last line adds the working rules' "after a merge" steps (update your own
  open PR branches from the default branch, follow-ups go on a new branch);
- if the checked-out branch's PR is already merged, it says so: never push to that branch.

Fails open: outside a GitHub repo, or if `gh` is missing or slow, it prints nothing and exits 0
(after a gh failure it says so once per session).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

CACHE_DIR = Path.home() / ".claude" / "hook-cache" / "github_state"
GH_TIMEOUT_S = 3.5  # the three gh calls run in parallel and must fit the hook's 5 s timeout


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


def current_branch(cwd: str) -> str | None:
    try:
        branch = run(["git", "branch", "--show-current"], cwd).strip()
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return None
    return branch or None


def read_state(repo: str, cwd: str, branch: str | None) -> dict:
    since = (datetime.now(UTC) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    jobs = {
        "open": ["gh", "pr", "list", "-R", repo, "--state", "open",
                 "--json", "number,title,labels,isDraft", "--limit", "30"],
        "merged": ["gh", "pr", "list", "-R", repo, "--state", "merged",
                   "--search", f"merged:>={since}", "--json", "number,mergedAt", "--limit", "20"],
    }
    if branch:
        jobs["branch"] = ["gh", "pr", "list", "-R", repo, "--head", branch, "--state", "all",
                          "--json", "number,state", "--limit", "5"]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {name: pool.submit(run, cmd, cwd) for name, cmd in jobs.items()}
        return {name: json.loads(future.result()) for name, future in futures.items()}


def describe(state: dict, branch: str | None) -> tuple[str, list[int], str]:
    """(state line, merged PR numbers, warning about the checked-out branch or '')."""
    open_prs = sorted(state["open"], key=lambda p: p["number"])
    merged = sorted(state["merged"], key=lambda p: p["mergedAt"], reverse=True)
    opened = ", ".join(
        f"#{pr['number']}{' (draft)' if pr.get('isDraft') else ''} {pr['title'][:50]}"
        for pr in open_prs
    ) or "none"
    needs_you = ", ".join(
        f"#{pr['number']}"
        for pr in open_prs
        if "needs-you" in {label["name"] for label in pr.get("labels", [])}
    ) or "none"
    recent = ", ".join(f"#{pr['number']} ({pr['mergedAt'][11:16]}Z)" for pr in merged[:5]) or "none"
    if len(merged) > 5:
        recent += f" and {len(merged) - 5} more"
    line = f"open PRs: {opened} · needs-you PRs: {needs_you} · merged in last 24h: {recent}"

    warning = ""
    prs = state.get("branch") or []
    if branch and prs and not any(pr["state"] == "OPEN" for pr in prs):
        number = prs[0]["number"]
        if any(pr["state"] == "MERGED" for pr in prs):
            warning = (
                f"Branch `{branch}` belongs to PR #{number}, which is already merged: do not push "
                "to it; put follow-up work on a new branch off the default branch."
            )
    return line, [pr["number"] for pr in merged], warning


def load_cache(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


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
    branch = current_branch(cwd)
    merged_numbers: list[int] | None = None
    try:
        line, merged_numbers, warning = describe(read_state(repo, cwd, branch), branch)
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        line = (
            f"could not read GitHub state ({type(exc).__name__}); "
            "check with gh before reporting PR status"
        )
        warning = ""

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache = CACHE_DIR / f"{session}-{hashlib.sha1(repo.encode()).hexdigest()[:8]}.json"
    previous = load_cache(cache)
    full = f"{line}|{warning}"
    if previous.get("full") == full:
        return

    notes = [warning] if warning else []
    seen = set(previous.get("merged") or [])
    new_merges = [n for n in (merged_numbers or []) if n not in seen]
    if previous and new_merges:
        listed = ", ".join(f"#{n}" for n in sorted(new_merges))
        notes.append(
            f"New merges since your last check: {listed}. After a merge: fetch the default "
            "branch and merge it into your own open PR branches if they now conflict (no rebase, "
            "no force-push); anything you believed open or waiting may have changed."
        )
    cache.write_text(
        json.dumps({"full": full, "merged": merged_numbers or previous.get("merged") or []}),
        encoding="utf-8",
    )

    now = datetime.now().astimezone().strftime("%H:%M")
    context = " ".join(
        [f"GitHub state of {repo} at {now} (changed since you last saw it): {line}.", *notes]
    )
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": context,
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken hook must never block the user's message
        pass
