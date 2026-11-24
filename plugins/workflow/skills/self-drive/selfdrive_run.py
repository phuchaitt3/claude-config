#!/usr/bin/env python3
"""Cost of one self-drive run that spans several chats, found from the transcripts (no registry).

Usage: python selfdrive_run.py REPO [--date YYYY-MM-DD] [--gap-hours N] [--log FILE] [--projects DIR]
       (REPO is the repository folder name, for example book-rag-app)

Without --date it lists the runs found for REPO and prints nothing else. With --date it prints one JSON
line for the run whose first loop chat started on that local date.

How chats are tied to a run (user's decision, 2026-11-24: a run spans many chats and sub-agents, and
two repositories can run at once):
- Loop chats: transcripts in REPO's project folders whose first prompt starts "Self-drive overnight in
  REPO" (the prompt `scripts/selfdrive.ps1` sends). Loop chats whose starts are less than --gap-hours
  apart (default 14) are one run, so a successor after a context reset joins its run.
- Workers: other chats in REPO's project folders (the main checkout and its worktrees) that start inside
  the run's window and whose first prompt names "issue #N". An interactive chat of yours in the same
  repo that opens with such a prompt would be counted too; the output lists every worker so it shows.
- Sub-agents: each chat's own `subagents/` transcripts.
A run of another repository never matches, because the project folder name carries the repo name.

Cost: "own_M" is the run's weighted tokens (units as in selfdrive_cost.py); "foreign_M" is what every
other chat on this machine used in the same window. "week_net_pct" is the whole account's weekly-quota
change in the window (last reading minus the one before it; "week_pct" sums every rise and counts
noise between chats' readings, so do not trust it); "week_pct_attrib" scales the net change by the run's share of the weighted tokens, which
leaves out your own chats but treats a token as costing the same whichever chat spent it. "week_pct_est"
is own tokens over the calibration (selfdrive_cost.py --calibrate). Tokens from other devices are
not in the transcripts, so every figure is a lower bound on the run's share.
"""
import glob, importlib.util, json, os, re, sys
from datetime import datetime
from pathlib import Path

_spec = importlib.util.spec_from_file_location("selfdrive_cost", Path(__file__).with_name("selfdrive_cost.py"))
cost = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cost)

PROJECTS = os.path.join(os.path.expanduser("~"), ".claude", "projects")
LOOP_PROMPT = "Self-drive overnight in "
ISSUE = re.compile(r"issue #(\d+)", re.I)


def _epoch(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()


def head(path):
    """(first user prompt text, first timestamp) of a transcript, or ("", None)."""
    prompt, first = "", None
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        if first is None and o.get("timestamp"):
            first = o["timestamp"]
        m = o.get("message")
        if isinstance(m, dict) and m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, list):
                c = " ".join(p.get("text", "") for p in c if isinstance(p, dict))
            prompt = (c or "").strip()
            break
    return prompt, first


def repo_chats(repo, projects=PROJECTS):
    """Top-level transcripts in project folders named after REPO: [(path, session id, prompt, first ts)]."""
    out = []
    for d in glob.glob(os.path.join(projects, "*")):
        if repo.lower() not in os.path.basename(d).lower():
            continue
        for p in glob.glob(os.path.join(d, "*.jsonl")):
            prompt, first = head(p)
            if first:
                out.append((p, os.path.basename(p)[:-6], prompt, first))
    return sorted(out, key=lambda c: c[3])


def group_runs(repo, chats, gap_hours=14.0):
    """Runs as dicts {loops, workers, start, end}; start/end are ISO times of the first and last model call."""
    loops = [c for c in chats if c[2].startswith(LOOP_PROMPT + repo)]
    others = [c for c in chats if c not in loops]
    runs = []
    for c in loops:
        if runs and _epoch(c[3]) - _epoch(runs[-1]["loops"][-1][3]) < gap_hours * 3600:
            runs[-1]["loops"].append(c)
        else:
            runs.append(dict(loops=[c], workers=[]))
    for r in runs:
        ends = []
        for c in r["loops"]:
            ends += scan_with_children(c[0])["ts"]
        r["start"], r["end"] = r["loops"][0][3], max(ends) if ends else r["loops"][0][3]
    for c in others:
        m = ISSUE.search(c[2][:300])
        if not m:
            continue
        for r in runs:
            if _epoch(r["start"]) <= _epoch(c[3]) <= _epoch(r["end"]):
                r["workers"].append(c)
                break
    for r in runs:
        ends = [r["end"]]
        for c in r["workers"]:
            ends += scan_with_children(c[0])["ts"]
        r["end"] = max(ends)
    return runs


def scan_with_children(path):
    """The chat's own transcript plus its sub-agents', merged; `subs` counts the sub-agent transcripts."""
    s = cost.scan(path)
    subs = glob.glob(os.path.join(path[:-6], "subagents", "*.jsonl"))
    for sp in subs:
        w = cost.scan(sp)
        s["calls"] += w["calls"]; s["w"] += w["w"]; s["ts"] += w["ts"]
    s["subs"] = len(subs)
    return s


def foreign_weighted(t0, t1, own_ids, projects=PROJECTS):
    """Weighted tokens of every chat on this machine, other than own_ids, with a call inside [t0, t1]."""
    seen, w = set(), 0.0
    for f in glob.glob(os.path.join(projects, "**", "*.jsonl"), recursive=True):
        rel = os.path.relpath(f, projects).split(os.sep)
        sid = rel[1][:-6] if len(rel) == 2 else rel[1]
        if sid in own_ids:
            continue
        for line in open(f, encoding="utf-8", errors="ignore"):
            if '"usage"' not in line:
                continue
            try:
                o = json.loads(line)
                m, t = o["message"], _epoch(o["timestamp"])
                u = m["usage"]
            except (ValueError, KeyError, TypeError):
                continue
            if t0 <= t <= t1 and m.get("id") not in seen and m.get("model") != "<synthetic>":
                seen.add(m.get("id"))
                w += sum(u.get(k, 0) * f2 for k, f2 in cost.W.items())
    return w


def net_rise(log, start, end, key="week"):
    """Last reading minus the reading just before the window, in one quota window (a reset gives None).

    Each chat reads the quota from its own status line, so readings from different chats can disagree
    by a few points (24, 23, 24, 19 within a quarter of an hour). Summing every rise counts that noise;
    the net rise between two readings does not, so it is the figure to trust.
    """
    t0, t1 = _epoch(start), _epoch(end)
    try:
        rows = sorted((r for r in (json.loads(x) for x in open(log, encoding="utf-8") if x.strip())
                       if key in r and "t" in r), key=lambda r: r["t"])
    except (OSError, ValueError):
        return None
    before = [r for r in rows if r["t"] < t0]
    inside = [r for r in rows if t0 <= r["t"] <= t1]
    if not before or not inside or inside[-1][key + "_resets"] != before[-1][key + "_resets"]:
        return None
    return round(inside[-1][key] - before[-1][key], 1)


def summarise(repo, run, quota_log=cost.QUOTA_LOG, projects=PROJECTS, prs=True):
    chats = run["loops"] + run["workers"]
    ids = {c[1] for c in chats}
    own, subs = 0.0, 0
    for c in chats:
        s = scan_with_children(c[0])
        own += s["w"]; subs += s["subs"]
    t0, t1 = _epoch(run["start"]), _epoch(run["end"])
    foreign = foreign_weighted(t0, t1, ids, projects)
    out = dict(
        repo=repo, start=run["start"], end=run["end"],
        loops=[c[1][:8] for c in run["loops"]],
        workers=[dict(session=c[1][:8], issue=int(ISSUE.search(c[2][:300]).group(1))) for c in run["workers"]],
        subagent_transcripts=subs, own_M=round(own / 1e6, 2), foreign_M=round(foreign / 1e6, 2),
        own_share=round(own / (own + foreign), 2) if own + foreign else None,
    )
    cal = cost.calibrate(quota_log)
    if cal:
        out["week_pct_est"] = round(own / 1e6 / cal["M_per_week_pct"], 1)
    q = cost.quota_used(quota_log, run["start"], run["end"])
    if q:
        out.update(q)
        out["week_net_pct"] = net_rise(quota_log, run["start"], run["end"])
        if out["own_share"] is not None and out["week_net_pct"] is not None:
            out["week_pct_attrib"] = round(out["week_net_pct"] * out["own_share"], 1)
    if prs:
        states = cost.run_prs(f"phuchaitt3/{repo}", run["start"], run["end"])
        merged = sum(1 for v in states.values() if v == "MERGED")
        out.update(prs_opened=len(states), prs_merged=merged, prs=states)
        if merged and "week_pct_attrib" in out:
            out["week_pct_attrib_per_merged_pr"] = round(out["week_pct_attrib"] / merged, 2)
    return out


def local_date(ts):
    return datetime.fromtimestamp(_epoch(ts)).strftime("%Y-%m-%d")


def main(argv):
    repo = date = log = None
    gap, projects = 14.0, PROJECTS
    it = iter(argv)
    for a in it:
        if a == "--date":
            date = next(it)
        elif a == "--gap-hours":
            gap = float(next(it))
        elif a == "--log":
            log = next(it)
        elif a == "--projects":
            projects = next(it)
        else:
            repo = a
    if not repo:
        sys.exit(__doc__)
    runs = group_runs(repo, repo_chats(repo, projects), gap)
    if not date:
        for r in runs:
            print(local_date(r["start"]), r["start"], "->", r["end"], "loops", len(r["loops"]), "workers", len(r["workers"]))
        return
    pick = [r for r in runs if local_date(r["start"]) == date]
    if not pick:
        sys.exit(f"no {repo} run starting on {date}")
    line = json.dumps(summarise(repo, pick[0], projects=projects))
    print(line)
    if log:
        with open(log, "a", encoding="utf-8") as f:
            f.write(line + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
