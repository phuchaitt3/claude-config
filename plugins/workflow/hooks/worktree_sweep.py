"""SessionStart hook: remove task worktrees whose pull request has merged and that hold nothing to lose.

The rule "remove a worktree after its PR merges" lived only in a project's RULES.md, with no
trigger at merge time and no owner (the author has moved on when the reviewer merges), so
worktrees piled up. Claude Code's own sweep skips worktrees made with `git worktree add`, which is
how the multi-chat skill makes them. Acts only where the main checkout has a handoff folder.

At most every 6 hours per repository it starts a detached worker. The worker removes a linked
worktree only when every check passes: not locked; its branch has no open PR and a PR merged over
2 hours ago (the liveness window); HEAD is in that PR or on the default branch; `git status` shows
nothing; and its ignored files are only ones a tool regenerates. Removal is `git worktree remove`
without `--force`, so git refuses anything else, and the branch is kept. Every decision is logged;
the next session start shows one line when worktrees were removed.

`python worktree_sweep.py sweep <main checkout> --dry-run` prints the decisions and changes nothing.
"""

from __future__ import annotations

import fnmatch
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _gitcmd import (
    CACHE_ROOT, default_branch, git, git_ok, main_checkout_of, opted_in, repo_key, spawn_detached,
)

CACHE = CACHE_ROOT / "worktree_sweep"
INTERVAL_S = 6 * 60 * 60
MIN_AGE = timedelta(hours=2)
# Ignored files a tool rebuilds; anything else ignored (a `.env.local`, data) blocks removal.
REGENERABLE = ("node_modules", ".venv", "venv", "__pycache__", ".next", ".pytest_cache",
               ".mypy_cache", ".ruff_cache", ".turbo", "dist", "build", "coverage", "htmlcov",
               ".coverage", "*.egg-info", "*.tsbuildinfo", "next-env.d.ts", "settings.local.json")


@dataclass
class Worktree:
    path: str
    head: str = ""
    branch: str = ""
    locked: bool = False
    prunable: bool = False


@dataclass
class Prs:
    merged: dict[str, list[dict]] = field(default_factory=dict)  # branch -> merged PRs
    open: set[str] = field(default_factory=set)


def parse_worktrees(porcelain: str) -> list[Worktree]:
    """The linked worktrees in `git worktree list --porcelain` (the main checkout is dropped)."""
    trees: list[Worktree] = []
    for block in porcelain.strip().split("\n\n"):
        tree: Worktree | None = None
        for line in block.splitlines():
            key, _, value = line.partition(" ")
            if key == "worktree":
                tree = Worktree(value)
            elif tree is None:
                continue
            elif key == "HEAD":
                tree.head = value
            elif key == "branch":
                tree.branch = value.removeprefix("refs/heads/")
            elif key == "locked":
                tree.locked = True
            elif key == "prunable":
                tree.prunable = True
        if tree:
            trees.append(tree)
    return trees[1:]


def read_prs(main: Path) -> Prs:
    def gh(*args: str) -> list[dict]:
        out = subprocess.run(
            ["gh", "pr", "list", *args], cwd=str(main), capture_output=True, text=True,
            encoding="utf-8", timeout=60, check=True,
        ).stdout
        return json.loads(out)

    prs = Prs()
    for pr in gh("--state", "merged", "--limit", "300", "--json",
                 "number,headRefName,headRefOid,mergedAt"):
        prs.merged.setdefault(pr["headRefName"], []).append(pr)
    prs.open = {pr["headRefName"] for pr in gh("--state", "open", "--limit", "200", "--json",
                                                "headRefName")}
    return prs


def _irreplaceable(tree: Worktree) -> list[str]:
    out = git(["status", "--porcelain", "--ignored=matching", "--untracked-files=normal"],
              tree.path, timeout=60)
    keep: list[str] = []
    for line in out.splitlines():
        if not line.startswith("!! "):
            continue
        name = line[3:].strip().strip('"').rstrip("/").rsplit("/", 1)[-1]
        if not any(fnmatch.fnmatch(name, pattern) for pattern in REGENERABLE):
            keep.append(line[3:].strip())
    return keep


def decide(tree: Worktree, prs: Prs, target: str, now: datetime) -> tuple[bool, str]:
    """(remove?, reason) for one worktree."""
    if tree.locked:
        return False, "locked"
    if not tree.branch:
        return False, "detached HEAD"
    if tree.branch in prs.open:
        return False, "open PR"
    merged = prs.merged.get(tree.branch)
    if not merged:
        return False, "no merged PR"
    latest = max(merged, key=lambda pr: pr["mergedAt"])
    merged_at = datetime.fromisoformat(latest["mergedAt"].replace("Z", "+00:00"))
    if now - merged_at < MIN_AGE:
        return False, f"PR #{latest['number']} merged under {MIN_AGE} ago"
    in_pr = any(
        tree.head == pr["headRefOid"]
        or git_ok(["merge-base", "--is-ancestor", "HEAD", pr["headRefOid"]], tree.path)
        for pr in merged
    )
    if not in_pr and not git_ok(["merge-base", "--is-ancestor", "HEAD", target], tree.path):
        return False, f"commits not in PR #{latest['number']} or {target}"
    if git(["status", "--porcelain"], tree.path, timeout=60).strip():
        return False, "uncommitted or untracked files"
    keep = _irreplaceable(tree)
    if keep:
        return False, "ignored files a tool may not rebuild: " + ", ".join(keep[:5])
    return True, f"PR #{latest['number']} merged {latest['mergedAt'][:10]}"


def log_path(main: Path) -> Path:
    return CACHE / f"{repo_key(main)}.log"


def sweep(main: Path, dry_run: bool, now: datetime | None = None) -> list[str]:
    """Remove the worktrees `decide` clears; return one line per decision."""
    now = now or datetime.now(timezone.utc)
    target = f"origin/{default_branch(main)}"
    git_ok(["fetch", "origin", "--quiet", "--prune"], main, timeout=60)
    prs = read_prs(main)
    lines: list[str] = []
    trees = parse_worktrees(git(["worktree", "list", "--porcelain"], main))
    for tree in trees:
        if tree.prunable:
            lines.append(f"prune {tree.path} [{tree.branch}] folder is gone")
            continue
        try:
            remove, reason = decide(tree, prs, target, now)
        except (OSError, RuntimeError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
            remove, reason = False, f"could not check: {exc}"
        if remove and not dry_run:
            if git_ok(["worktree", "remove", tree.path], main, timeout=600):
                left = " (left a non-empty folder; not deleted)" if Path(tree.path).exists() else ""
                reason += left
            else:
                remove, reason = False, "git refused to remove it"
        lines.append(f"{'remove' if remove else 'keep'} {tree.path} [{tree.branch}] {reason}")
    if any(t.prunable for t in trees) and not dry_run:
        git_ok(["worktree", "prune"], main)
    return lines


def run_sweep(main: Path) -> None:
    lines = sweep(main, dry_run=False)
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path = log_path(main)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as log:
        log.writelines(f"{stamp} {line}\n" for line in lines)
    removed = sum(line.startswith("remove ") for line in lines)
    if removed:
        state = CACHE / f"{repo_key(main)}.pending"
        state.write_text(str(removed + _pending(state)), encoding="utf-8")


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
    removed = _pending(state)
    if not removed:
        return None
    state.unlink(missing_ok=True)
    return (f"worktree_sweep removed {removed} worktree(s) whose PR had merged; branches are kept "
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
