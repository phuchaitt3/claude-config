"""Rank a repo's open issues bottleneck-first, so a chat picks the task that unblocks the most work.

Run from inside the repository: `python <this skill's folder>/next_task.py [--limit N]`.
With `--status [--handoff PATH]` it is a self-drive round's whole sync in one call: it pulls the
handoff repo (`git -C PATH pull --rebase`) when given, then prints the open PRs, the claimed issues,
the worktrees and the ranked startable issues, so the loop chat makes one tool call, not several.

Reads open issues and their GitHub issue dependencies ("blocked by" / "blocking" links) with one
GraphQL call, then prints the issues a chat may start, best first (user's decision, 2026-11-15):

0. `priority:first`: the user's override (2026-11-17), ahead of everything else, including resume work;
   among several, the oldest. A blocked, `claimed` or `needs-you` issue is still left out;
1. resume-relevant: an issue labelled `resume:1` to `resume:6` (set by the triage pass, TRIAGE.md),
   or one that blocks such an issue, directly or through others (it takes the best label it unblocks);
   by that label, then the `gap:<group>` rank in ~/.claude/resume-gaps.md, then the shorter chain
   to the resume issue, then the oldest;
2. `priority:now`, or any issue that blocks 2 or more open issues (a bottleneck);
3. `priority:next`; then `priority:later`; then unlabelled;
within groups 2 and 3, the issue that blocks the most open issues, directly or through others, then
the oldest. With no `resume:` labels in the repo, the order is groups 2 and 3 alone.

Issues that are blocked by an open issue, or labelled `claimed`, `needs-you` or `parked`, are left out.
It also prints three kinds of fix-up for the chat to make (advisory: none skips or blocks an issue;
standard: findings/backlog-label-lint, checked 2026-11-18): a bottleneck not labelled
`priority:now`, a "Blocked by #n" line in an issue body with no matching dependency link
(text is invisible to GitHub's `is:blocking` search and to this script), and an `adr-review`
issue without `needs-you` (an owner review; an overnight run cannot do it).
With `--status` it also prints `STALE CLAIM? #n: <reason>` above the ranked list when the best
claimed issue would outrank every startable one and the claim sweep's test (`hooks/claim_sweep.py`,
dry run) says its claim is stale; the round then runs `claim_sweep.py sweep` at once (2026-11-18).
(standard: findings/bottleneck-tasks, checked 2026-11-01)

An issue labelled `heavy` (its finish needs a GPU, a full test suite, a large model load or a Compose
stack; set by triage or when filed) is held back while `gpu_run.py status` shows the GPU lock held or
free memory under its 4 GB gate: a `HEAVY HOLD:` line names the skipped issue and the light one to
take instead, and the next round checks again (#26, 2026-11-18).
The label is learned from evidence, not set by an up-front pass (#28, 2026-11-18; standard:
findings/heavy-task-tagging, checked 2026-11-18): `--wait-evidence` prints each lock start in the
`gpu_run.py` events that waited WAIT_HEAVY_S (10 minutes) or more, so the loop can label the issue
that worker was on; a worker killed for low memory is the other evidence (SKILL.md, "Heavy-task hold").
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BOTTLENECK_MIN = 2  # an issue blocking this many open issues counts as priority:now
SKIP_LABELS = {"claimed", "needs-you", "parked"}
OWNER_REVIEW = "adr-review"  # an owner review: an overnight run cannot do it, so it needs `needs-you`
WAIT_HEAVY_S = 600  # a lock wait this long is evidence the issue is heavy (#28; 10 min = the run-estimate bar)
HEAVY = "heavy"  # finish needs a heavy local job (GPU, full test suite, large model, Compose stack)
FIRST = "priority:first"  # the user's override: runs before resume work and everything else
TIERS = {"priority:now": 0, "priority:next": 1, "priority:later": 2}
TEXT_DEP = re.compile(r"\bblocked by\s+#(\d+)", re.IGNORECASE)
RESUME = re.compile(r"^resume:([1-6])$")  # kinds of resume work, 1 best; meanings in TRIAGE.md
GAP_LINE = re.compile(r"^\s*\d+\.\s+`([a-z0-9-]+)`")  # a ranked group line in resume-gaps.md
GAPS_FILE = Path.home() / ".claude" / "resume-gaps.md"
NO_RANK = 99


def gap_ranks(path: Path = GAPS_FILE) -> dict[str, int]:
    """Group slug -> rank (0 best) from the numbered lines of the local resume-gaps file."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    slugs = [m.group(1) for m in map(GAP_LINE.match, lines) if m]
    return {s: i for i, s in enumerate(slugs)}


def resume_key(labels: set[str], ranks: dict[str, int]) -> tuple[int, int] | None:
    """(resume kind, gap rank) of an issue's own labels, or None when it has no resume label."""
    kinds = [int(m.group(1)) for m in map(RESUME.match, labels) if m]
    if not kinds:
        return None
    gap = min((ranks.get(x[4:], NO_RANK) for x in labels if x.startswith("gap:")), default=NO_RANK)
    return (min(kinds), gap)

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


def depths(issues: list[dict]) -> dict[int, dict[int, int]]:
    """For each open issue, the open issues it blocks mapped to the shortest chain length to each."""
    direct = {i["number"]: _open_numbers(i["blocking"]) for i in issues}
    result: dict[int, dict[int, int]] = {}
    for start in direct:
        seen: dict[int, int] = {}
        frontier, d = list(direct[start]), 1
        while frontier:
            nxt = []
            for n in frontier:
                if n == start or n in seen:
                    continue
                seen[n] = d
                nxt.extend(direct.get(n, ()))
            frontier, d = nxt, d + 1
        result[start] = seen
    return result


def rank(issues: list[dict], ranks: dict[str, int] | None = None) -> tuple[list[dict], list[str]]:
    """The startable issues, best first, and the fix-ups to make."""
    ranked, fixups, _ = rank_with_claimed(issues, ranks)
    return ranked, fixups


def rank_with_claimed(
    issues: list[dict], ranks: dict[str, int] | None = None
) -> tuple[list[dict], list[str], list[dict]]:
    """`rank`, plus the unblocked `claimed` issues (not `needs-you`) ranked the same way, best first."""
    ranks = gap_ranks() if ranks is None else ranks
    blocks = downstream(issues)
    chain = depths(issues)
    numbers = {i["number"] for i in issues}
    labels_of = {i["number"]: {lab["name"] for lab in i["labels"]["nodes"]} for i in issues}
    own = {n: resume_key(labs, ranks) for n, labs in labels_of.items()}
    ranked, fixups, held = [], [], []
    for issue in issues:
        n = issue["number"]
        labels = labels_of[n]
        fan = len(blocks[n])
        linked = {b["number"] for b in issue["blockedBy"]["nodes"]}
        for m in sorted({int(x) for x in TEXT_DEP.findall(issue["body"] or "")} - linked):
            if m in numbers:
                fixups.append(f"#{n}: body says 'Blocked by #{m}' but has no dependency link; add it")
        if OWNER_REVIEW in labels and "needs-you" not in labels:
            fixups.append(f"#{n}: labelled {OWNER_REVIEW} (an owner review) without needs-you; add it")
        if fan >= BOTTLENECK_MIN and "priority:now" not in labels:
            fixups.append(f"#{n}: blocks {fan} open issues; label it priority:now")
        if _open_numbers(issue["blockedBy"]) or labels & SKIP_LABELS:
            if "claimed" in labels and "needs-you" not in labels and not _open_numbers(issue["blockedBy"]):
                held.append(entry(issue, labels, fan, own, chain))
            continue
        ranked.append(entry(issue, labels, fan, own, chain))
    ranked.sort(key=sort_key)
    held.sort(key=sort_key)
    return ranked, fixups, held


def entry(issue: dict, labels: set[str], fan: int, own: dict, chain: dict) -> dict:
    n = issue["number"]
    tier = 0 if fan >= BOTTLENECK_MIN else min((TIERS[x] for x in labels if x in TIERS), default=3)
    # resume: own label (chain 0) or the best resume issue it unblocks (chain = its distance)
    options = [(*own[n], 0)] if own[n] else []
    options += [(*own[m], d) for m, d in chain[n].items() if own.get(m)]
    resume = min(options) if options else None
    return {"number": n, "title": issue["title"], "tier": tier, "blocks": fan,
            "resume": resume, "first": FIRST in labels, "heavy": HEAVY in labels, "createdAt": issue["createdAt"]}


def stale_warning(ranked: list[dict], held: list[dict], decisions: list[str]) -> list[str]:
    """`STALE CLAIM?` line when the best claimed issue outranks every startable one and its claim is
    stale by `claim_sweep.decide` (`decisions` = the lines of a dry-run sweep, "release #n reason")."""
    if not held or (ranked and sort_key(ranked[0]) < sort_key(held[0])):
        return []
    n = held[0]["number"]
    for line in decisions:
        if line.startswith(f"release #{n} "):
            return [f"STALE CLAIM? #{n}: {line.split(' ', 2)[2]}; run "
                    "`python <plugin>/hooks/claim_sweep.py sweep <main checkout>` now"]
    return []


def stale_decisions(repo: str) -> list[str]:
    """Dry-run decisions of the claim sweep for `repo` (same test the hourly sweep applies)."""
    hooks = str(Path(__file__).resolve().parents[2] / "hooks")
    sys.path.insert(0, hooks)
    try:
        import claim_sweep  # noqa: PLC0415
    finally:
        sys.path.remove(hooks)
    return claim_sweep.sweep(Path.cwd(), dry_run=True, repo=repo)


def sort_key(r: dict) -> tuple:
    if r.get("first"):
        return (-1, 0, 0, 0, 0, 0, r["createdAt"])
    if r["resume"]:
        return (0, *r["resume"], 0, 0, r["createdAt"])
    return (1, 0, 0, 0, r["tier"], -r["blocks"], r["createdAt"])


NAMES = ["now", "next", "later", "unlabelled"]


def tag(r: dict) -> str:
    """The label a ranked entry is shown with: first, a tier, or resume:<kind>, then [heavy]."""
    if r.get("first"):
        base = "first"
    elif not r["resume"]:
        base = NAMES[r["tier"]]
    else:
        kind, _, d = r["resume"]
        base = f"resume:{kind}" + (f" (unblocks, chain {d})" if d else "")
    return base + (" [heavy]" if r.get("heavy") else "")


def render(ranked: list[dict], limit: int) -> list[str]:
    """One line per startable issue up to `limit`, then how many were cut, so none look absent."""
    lines = [f"#{r['number']}\t{tag(r)}\tblocks {r['blocks']}\t{r['title']}" for r in ranked[:limit]]
    if len(ranked) > limit:
        lines.append(f"... {len(ranked) - limit} more not shown (--limit)")
    if not ranked:
        lines.append("no startable issue")
    return lines


GPU_RUN = Path.home() / "claude-config" / "scripts" / "gpu_run.py"
MEM_LINE = re.compile(r"memory free[^:]*:\s*([\d.]+) GB; heavy jobs start at ([\d.]+) GB")


def machine_clear(status_text: str) -> tuple[bool, str]:
    """(clear?, reason) from `gpu_run.py status` output: the GPU lock must be free and free memory
    at or over the 4 GB gate that `gpu_run.py` applies to heavy jobs (#26, 2026-11-18)."""
    for line in status_text.splitlines():
        if line.startswith("GPU held by"):
            return False, line.strip()
        m = MEM_LINE.search(line)
        if m and float(m.group(1)) < float(m.group(2)):
            return False, f"free memory {m.group(1)} GB is under the {m.group(2)} GB gate"
    return True, "machine clear"


def pick(ranked: list[dict], clear: bool) -> tuple[dict | None, list[dict]]:
    """The issue to take and the heavy issues skipped to reach it. With the machine clear, the top
    one; otherwise the first that is not `heavy` (None when every startable issue is heavy)."""
    if clear:
        return (ranked[0] if ranked else None), []
    skipped: list[dict] = []
    for r in ranked:
        if r.get("heavy"):
            skipped.append(r)
        else:
            return r, skipped
    return None, skipped


def hold_lines(ranked: list[dict], clear: bool, reason: str) -> list[str]:
    """`HEAVY HOLD` lines for the round when the machine is not clear and a heavy issue ranks first."""
    take, skipped = pick(ranked, clear)
    if not skipped:
        return []
    nums = ", ".join(f"#{r['number']}" for r in skipped)
    nxt = f"take #{take['number']}" if take else "no light issue to take"
    return [f"HEAVY HOLD: {reason}; skipped heavy {nums} (retry next round; put it in the summary); {nxt}"]


def long_waits(events: list[dict], threshold: int = WAIT_HEAVY_S) -> list[str]:
    """One line per `start` event in gpu_run.py's log that waited `threshold` seconds or more for a lock
    (resource, wait, purpose, folder): the evidence that the issue being worked was heavy (#28)."""
    return [f"HEAVY EVIDENCE: waited {e['waited_s']} s on the {e.get('resource', 'gpu')} lock: "
            f"{e.get('purpose') or '-'} ({e.get('cwd') or '-'})"
            for e in events if e.get("event") == "start" and (e.get("waited_s") or 0) >= threshold]


def read_wait_events(days: int) -> list[dict]:
    """Events of the last `days` days from gpu_run.py's log (same file and cutoff as `gpu_run.py report`)."""
    spec = importlib.util.spec_from_file_location("gpu_run", GPU_RUN)
    if spec is None or spec.loader is None:
        return []
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.read_events(days)


PICKS_LOG = Path.home() / ".claude" / "overnight-picks.jsonl"


def candidates_record(repo: str, ranked: list[dict], clear: bool, reason: str, now: str, top: int = 5) -> dict:
    """The `candidates` log line (#27): the first `top` startable issues with the label each had when
    ranked, the heavy ones skipped for a HEAVY HOLD, and the issue the hold rule would take."""
    take, skipped = pick(ranked, clear)
    return {"event": "candidates", "ts": now, "repo": repo, "machine": reason,
            "candidates": [{"n": r["number"], "tag": tag(r), "blocks": r["blocks"]} for r in ranked[:top]],
            "heavy_hold": [r["number"] for r in skipped], "default_pick": take["number"] if take else None}


def append_log(rec: dict, path: Path = PICKS_LOG) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def machine_status() -> str:
    result = subprocess.run([sys.executable, str(GPU_RUN), "status"], capture_output=True,
                            text=True, encoding="utf-8", timeout=30)
    return result.stdout


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


def status(repo: str, issues: list[dict], handoff: str | None,
           ranked: list[dict] | None = None, held: list[dict] | None = None) -> list[str]:
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
    if held:
        try:
            lines += stale_warning(ranked or [], held, stale_decisions(repo))
        except Exception as exc:  # the warning is advice; never break the round sync  # noqa: BLE001
            lines.append(f"(stale-claim check failed: {str(exc)[:120]})")
    lines.append("== startable issues")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--repo", help="owner/name; default: the repo of the current folder")
    parser.add_argument("--status", action="store_true",
                        help="print the whole round sync: open PRs, claims, worktrees, then issues")
    parser.add_argument("--log-picks", action="store_true",
                        help="append this ranking to ~/.claude/overnight-picks.jsonl (local, never committed)")
    parser.add_argument("--wait-evidence", type=float, metavar="DAYS",
                        help="print the lock waits of 10 minutes or more in the last DAYS days (heavy evidence) and exit")
    parser.add_argument("--handoff", help="with --status: a handoff repo to pull first")
    args = parser.parse_args()
    if args.wait_evidence is not None:
        for line in long_waits(read_wait_events(args.wait_evidence)) or ["no lock wait over 10 minutes"]:
            print(line)
        return 0
    try:
        repo = args.repo or gh(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]).strip()
        issues = fetch(repo)
        ranked, fixups, held = rank_with_claimed(issues)
        if args.status:
            for line in status(repo, issues, args.handoff, ranked, held):
                print(line)
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"next_task: cannot read GitHub: {exc}", file=sys.stderr)
        return 1
    clear, reason = True, "no heavy issue ranked"
    if any(r.get("heavy") for r in ranked):
        try:
            clear, reason = machine_clear(machine_status())
        except (subprocess.TimeoutExpired, OSError):
            clear, reason = True, "machine status unreadable"
    if args.log_picks:
        try:
            append_log(candidates_record(repo, ranked, clear, reason,
                                         datetime.now(timezone.utc).isoformat(timespec="seconds")))
        except OSError as exc:  # a side record; never break the round
            print(f"(picks log failed: {exc})", file=sys.stderr)
    if any(r.get("heavy") for r in ranked):
        for line in hold_lines(ranked, clear, reason):
            print(line)
    for line in render(ranked, args.limit):
        print(line)
    for line in fixups:
        print(f"fix: {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
