"""Rank a repo's open issues bottleneck-first, so a chat picks the task that unblocks the most work.

Run from inside the repository: `python <this skill's folder>/next_task.py [--limit N]`.
With `--status [--handoff PATH]` it is a self-drive round's whole sync in one call: it pulls the
handoff repo (`git -C PATH pull --rebase`) when given, then prints the open PRs, the claimed issues,
the worktrees and the ranked startable issues, so the loop chat makes one tool call, not several.

Reads open issues and their GitHub issue dependencies ("blocked by" / "blocking" links) with one
GraphQL call, then prints the issues a chat may start, best first:

1. tier: `priority:now`, or any issue that blocks 2 or more open issues (a bottleneck); then
   `priority:next`; then `priority:later`; then unlabelled;
2. within a tier, the issue that blocks the most open issues, directly or through others;
3. then the oldest.

Issues that are blocked by an open issue, or labelled `claimed` or `needs-you`, are left out.
It also prints two kinds of fix-up for the chat to make: a bottleneck not labelled
`priority:now`, and a "Blocked by #n" line in an issue body with no matching dependency link
(text is invisible to GitHub's `is:blocking` search and to this script).
(standard: findings/bottleneck-tasks, checked 2026-11-01)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

BOTTLENECK_MIN = 2  # an issue blocking this many open issues counts as priority:now
SKIP_LABELS = {"claimed", "needs-you"}
TIERS = {"priority:now": 0, "priority:next": 1, "priority:later": 2}
TEXT_DEP = re.compile(r"\bblocked by\s+#(\d+)", re.IGNORECASE)

QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(states: OPEN, first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title body createdAt
        labels(first: 20) { nodes { name } }
        blockedBy(first: 50) { nodes { number state } }
        blocking(first: 50) { nodes { number state } }
      }
    }
  }
}
"""


def gh(args: list[str]) -> str:
    result = subprocess.run(
        ["gh", *args], capture_output=True, text=True, encoding="utf-8", timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip()[:300])
    return result.stdout


def fetch(repo: str) -> list[dict]:
    owner, name = repo.split("/", 1)
    issues: list[dict] = []
    cursor = None
    while True:
        args = ["api", "graphql", "-f", f"query={QUERY}", "-f", f"owner={owner}", "-f", f"name={name}"]
        if cursor:
            args += ["-f", f"cursor={cursor}"]
        page = json.loads(gh(args))["data"]["repository"]["issues"]
        issues += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return issues
        cursor = page["pageInfo"]["endCursor"]


def _open_numbers(conn: dict) -> set[int]:
    return {n["number"] for n in conn["nodes"] if n["state"] == "OPEN"}


def downstream(issues: list[dict]) -> dict[int, set[int]]:
    """For each open issue, every open issue it blocks, directly or through other issues."""
    direct = {i["number"]: _open_numbers(i["blocking"]) for i in issues}
    result: dict[int, set[int]] = {}
    for start in direct:
        seen: set[int] = set()
        stack = list(direct[start])
        while stack:
            n = stack.pop()
            if n in seen or n == start:
                continue
            seen.add(n)
            stack.extend(direct.get(n, ()))
        result[start] = seen
    return result


def rank(issues: list[dict]) -> tuple[list[dict], list[str]]:
    """The startable issues, best first, and the fix-ups to make."""
    blocks = downstream(issues)
    numbers = {i["number"] for i in issues}
    ranked, fixups = [], []
    for issue in issues:
        n = issue["number"]
        labels = {lab["name"] for lab in issue["labels"]["nodes"]}
        fan = len(blocks[n])
        linked = {b["number"] for b in issue["blockedBy"]["nodes"]}
        for m in sorted({int(x) for x in TEXT_DEP.findall(issue["body"] or "")} - linked):
            if m in numbers:
                fixups.append(f"#{n}: body says 'Blocked by #{m}' but has no dependency link; add it")
        if fan >= BOTTLENECK_MIN and "priority:now" not in labels:
            fixups.append(f"#{n}: blocks {fan} open issues; label it priority:now")
        if _open_numbers(issue["blockedBy"]) or labels & SKIP_LABELS:
            continue
        tier = 0 if fan >= BOTTLENECK_MIN else min((TIERS[x] for x in labels if x in TIERS), default=3)
        ranked.append({"number": n, "title": issue["title"], "tier": tier, "blocks": fan,
                       "createdAt": issue["createdAt"]})
    ranked.sort(key=lambda r: (r["tier"], -r["blocks"], r["createdAt"]))
    return ranked, fixups


def render(ranked: list[dict], limit: int) -> list[str]:
    """One line per startable issue up to `limit`, then how many were cut, so none look absent."""
    names = ["now", "next", "later", "unlabelled"]
    lines = [
        f"#{r['number']}\t{names[r['tier']]}\tblocks {r['blocks']}\t{r['title']}" for r in ranked[:limit]
    ]
    if len(ranked) > limit:
        lines.append(f"... {len(ranked) - limit} more not shown (--limit)")
    if not ranked:
        lines.append("no startable issue")
    return lines


def claimed(issues: list[dict]) -> list[str]:
    """One line per open issue labelled `claimed`, read from the issues already fetched."""
    return [
        f"#{i['number']}	{i['title']}"
        for i in sorted(issues, key=lambda i: i["number"])
        if "claimed" in {lab["name"] for lab in i["labels"]["nodes"]}
    ]


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=120)
    out = (result.stdout + result.stderr).strip()
    return out if result.returncode == 0 else f"FAILED ({result.returncode}): {out[:300]}"


def status(repo: str, issues: list[dict], handoff: str | None) -> list[str]:
    """The sync sections that come before the ranked issues in --status output."""
    lines: list[str] = []
    if handoff:
        lines += ["== handoff pull", run(["git", "-C", handoff, "pull", "--rebase", "-q"]) or "ok"]
    prs = json.loads(gh(["pr", "list", "-R", repo, "--state", "open", "--json",
                         "number,title,author,isDraft,reviewDecision,labels"]))
    lines.append(f"== open PRs ({len(prs)})")
    for pr in prs:
        tags = [lab["name"] for lab in pr["labels"]] + (["draft"] if pr["isDraft"] else [])
        lines.append(f"#{pr['number']}	{pr['author']['login']}	{pr['reviewDecision'] or '-'}"
                     f"	{','.join(tags) or '-'}	{pr['title']}")
    cl = claimed(issues)
    lines += [f"== claimed issues ({len(cl)})", *cl]
    lines += ["== worktrees", run(["git", "worktree", "list"])]
    lines.append("== startable issues")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--repo", help="owner/name; default: the repo of the current folder")
    parser.add_argument("--status", action="store_true",
                        help="print the whole round sync: open PRs, claims, worktrees, then issues")
    parser.add_argument("--handoff", help="with --status: a handoff repo to pull first")
    args = parser.parse_args()
    try:
        repo = args.repo or gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]).strip()
        issues = fetch(repo)
        ranked, fixups = rank(issues)
        if args.status:
            for line in status(repo, issues, args.handoff):
                print(line)
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"next_task: cannot read GitHub: {exc}", file=sys.stderr)
        return 1
    for line in render(ranked, args.limit):
        print(line)
    for line in fixups:
        print(f"fix: {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
