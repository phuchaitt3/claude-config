#!/usr/bin/env python3
"""Overnight picks log: record what a round took and summarise picks against the top-ranked issue.

Usage:
  python picks_log.py taken --issue N [--repo owner/name] [--skip N=reason ...]
  python picks_log.py report [--night YYYY-MM-DD] [log path]

The log is ~/.claude/overnight-picks.jsonl (local, never committed; #27, user's decision 2026-11-18).
Two events are written. `next_task.py --log-picks` writes `candidates` when the round ranks the
issues: the first five with their labels at that moment and the heavy ones a HEAVY HOLD skipped.
`taken` is written here once the round has chosen: the issue, its `resume:` and `priority:` labels
at that moment, and the reason for each skipped issue ranked above it (`--skip N=reason`; a heavy
skip needs none, the `candidates` line holds it). `report` pairs each `taken` with the latest
`candidates` line of the same repo and, per night (12:00 to 12:00 local time), prints the share of
picks that were the top-ranked startable issue (the first candidate not skipped for a HEAVY HOLD)
and the reason for each other pick. Labels are as the loop saw them, not today's re-triaged ones.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

LOG = Path.home() / ".claude" / "overnight-picks.jsonl"


def night_of(ts: str) -> str:
    """The night a UTC timestamp belongs to: local date of (time - 12 h), so 01:00 counts to the evening before."""
    local = datetime.fromisoformat(ts).astimezone()
    return (local - timedelta(hours=12)).date().isoformat()


def load(path: Path) -> list[dict]:
    recs = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                recs.append(json.loads(line))
            except ValueError:
                continue
    return recs


def summarise(recs: list[dict]) -> dict[str, list[dict]]:
    """Per night, one row per `taken` line: pick, top-ranked startable issue, and the reason when they differ."""
    last: dict[str, dict] = {}
    nights: dict[str, list[dict]] = defaultdict(list)
    for r in sorted(recs, key=lambda r: r["ts"]):
        if r.get("event") == "candidates":
            last[r["repo"]] = r
        elif r.get("event") == "taken":
            cand = last.get(r["repo"])
            held = set(cand["heavy_hold"]) if cand else set()
            top = next((c["n"] for c in cand["candidates"] if c["n"] not in held), None) if cand else None
            row = {"repo": r["repo"], "issue": r["issue"], "top": top, "labels": r.get("labels", []),
                   "heavy_hold": sorted(held), "reason": None}
            if top is not None and r["issue"] != top:
                why = r.get("skipped", {}).get(str(top))
                row["reason"] = why or "no reason recorded"
            elif top is None:
                row["reason"] = "no candidates line before the pick" if cand is None else "no startable candidate"
            nights[night_of(r["ts"])].append(row)
    return dict(nights)


def report(recs: list[dict], night: str | None = None) -> list[str]:
    nights = summarise(recs)
    lines = []
    for n in sorted(nights):
        if night and n != night:
            continue
        rows = nights[n]
        hits = [x for x in rows if x["reason"] is None]
        lines.append(f"night {n}: {len(rows)} picks, {len(hits)} were the top-ranked startable issue "
                     f"({round(100 * len(hits) / len(rows))}%)")
        for x in rows:
            if x["reason"] is not None:
                lines.append(f"  {x['repo']} took #{x['issue']} ({','.join(x['labels']) or 'no labels'}) "
                             f"over #{x['top']}: {x['reason']}")
            if x["heavy_hold"]:
                lines.append(f"  {x['repo']} HEAVY HOLD skipped {', '.join('#' + str(h) for h in x['heavy_hold'])}")
    return lines or ["no picks logged" + (f" for {night}" if night else "")]


def issue_labels(repo: str, number: int) -> list[str]:
    res = subprocess.run(["gh", "issue", "view", str(number), "-R", repo, "--json", "labels", "-q",
                          ".labels[].name"], capture_output=True, text=True, encoding="utf-8", timeout=60)
    names = res.stdout.split() if res.returncode == 0 else []
    return [x for x in names if x.startswith(("resume:", "priority:"))]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("taken")
    t.add_argument("--issue", type=int, required=True)
    t.add_argument("--repo")
    t.add_argument("--skip", action="append", default=[], metavar="N=reason")
    r = sub.add_parser("report")
    r.add_argument("--night")
    r.add_argument("path", nargs="?", type=Path, default=LOG)
    args = ap.parse_args(argv)
    if args.cmd == "report":
        print("\n".join(report(load(args.path), args.night)))
        return 0
    repo = args.repo or subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                                       capture_output=True, text=True, encoding="utf-8", timeout=60).stdout.strip()
    skipped = dict(s.split("=", 1) for s in args.skip if "=" in s)
    rec = {"event": "taken", "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "repo": repo,
           "issue": args.issue, "labels": issue_labels(repo, args.issue), "skipped": skipped}
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
