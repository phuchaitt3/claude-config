#!/usr/bin/env python3
"""Cost per merged PR for a self-drive run, read from Claude Code transcripts.

Usage: python selfdrive_cost.py --repo OWNER/NAME <session-id> [<successor-id> ...] [--log FILE] [--label TEXT]

Pass the loop chat's session id and any successor chats from a context reset.
Counts each chat plus its subagent workers. Prints one JSON line; --log appends it
to FILE (one run per line) so runs can be compared over time.

"weighted" is an estimate of quota use, in base-input-token units: input x1,
cache write x1.25, cache read x0.1, output x5 (API price ratios; how a subscription
quota is metered is not published). Compare runs with each other, not with the quota.

"week_pct" and "five_pct" are the percentage points of the weekly and 5-hour quota used in the run's
window, summed from ~/.claude/quota-log.jsonl (written by the quota_watch hook); they count the whole
account, so another chat running then is included, and the percentages are whole numbers, so a short
run reads coarsely. Missing if the log has no sample in the window.

"week_pct_est" is the run's weighted tokens divided by a calibration (weighted tokens per weekly
percentage point, `--calibrate`, from the quota log); it counts only this run, so it is the figure
to compare between runs, and it is as good as the calibration (see calibrate()).
`python selfdrive_cost.py --calibrate [LOG]` prints the calibration alone.

Read-only, except --log. PRs are those the bot opened in --repo between the run's first
and last model call (`gh pr list`, needs gh signed in); another chat in the same repo
in that window would be counted too, so run one loop per repo.
"""
import glob, json, os, subprocess, sys

QUOTA_LOG = os.path.join(os.path.expanduser("~"), ".claude", "quota-log.jsonl")
W = dict(input_tokens=1.0, cache_creation_input_tokens=1.25, cache_read_input_tokens=0.1, output_tokens=5.0)


def scan(path):
    seen, calls, w, ctx, ts = set(), 0, 0.0, [], []
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            o = json.loads(line)
        except ValueError:
            continue
        m = o.get("message")
        if not isinstance(m, dict):
            continue
        u = m.get("usage")
        if not u or m.get("id") in seen or m.get("model") == "<synthetic>":
            continue
        seen.add(m.get("id"))
        calls += 1
        w += sum(u.get(k, 0) * f for k, f in W.items())
        ctx.append(u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0))
        if o.get("timestamp"):
            ts.append(o["timestamp"])
    return dict(calls=calls, w=w, ctx=ctx, ts=ts)


def find(sid):
    f = glob.glob(os.path.join(os.path.expanduser("~"), ".claude", "projects", "*", sid + ".jsonl"))
    if not f:
        sys.exit("transcript not found: " + sid)
    return f[0]


def quota_used(log, start, end):
    """Percentage points of the weekly and 5-hour quota used between two ISO times, from the quota log.

    Sums the rises between consecutive samples inside the window (the last sample before the window
    is the baseline); a drop or a new reset time is a window reset and adds nothing. This is the whole
    account's use in that time, so another chat running then is counted too. Returns None if the log
    is missing or has no sample in the window.
    """
    from datetime import datetime
    t0 = datetime.fromisoformat(start.replace("Z", "+00:00")).timestamp()
    t1 = datetime.fromisoformat(end.replace("Z", "+00:00")).timestamp()
    try:
        rows = [json.loads(x) for x in open(log, encoding="utf-8") if x.strip()]
    except (OSError, ValueError):
        return None
    rows = sorted((r for r in rows if "t" in r), key=lambda r: r["t"])
    before = [r for r in rows if r["t"] < t0]
    inside = [r for r in rows if t0 <= r["t"] <= t1]
    if not inside:
        return None
    seq = before[-1:] + inside
    out = {}
    for key in ("week", "five"):
        pts = [r for r in seq if key in r]
        used = 0.0
        for a, b in zip(pts, pts[1:]):
            if b[key + "_resets"] == a[key + "_resets"] and b[key] > a[key]:
                used += b[key] - a[key]
        out[key + "_pct"] = round(used, 1)
        out[key + "_end"] = pts[-1][key] if pts else None
    out["quota_samples"] = len(inside)
    return out


def weighted_between(t0, t1):
    """Weighted tokens (same units as scan) of every chat on this machine between two epoch times."""
    from datetime import datetime
    seen, total = set(), 0.0
    for f in glob.glob(os.path.join(os.path.expanduser("~"), ".claude", "projects", "**", "*.jsonl"), recursive=True):
        for line in open(f, encoding="utf-8", errors="ignore"):
            if '"usage"' not in line:
                continue
            try:
                o = json.loads(line)
                m = o["message"]
                u, ts = m["usage"], o["timestamp"]
                t = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
            except (ValueError, KeyError, TypeError):
                continue
            if not t0 <= t <= t1 or m.get("id") in seen or m.get("model") == "<synthetic>":
                continue
            seen.add(m.get("id"))
            total += sum(u.get(k, 0) * x for k, x in W.items())
    return total


def calibrate(log):
    """Weighted tokens per percentage point of the weekly quota, from the quota log.

    For each weekly window, all chats' tokens between its first and last log sample divided by the
    rise in percent; pooled over windows. Needs a rise of at least 5 points to say anything.
    Tokens from other devices or claude.ai are not in the transcripts, so this overstates the cost
    of a point (understates the cap) by that share; model mix is not separated.
    """
    try:
        rows = [json.loads(x) for x in open(log, encoding="utf-8") if x.strip()]
    except (OSError, ValueError):
        return None
    groups = {}
    for r in sorted((r for r in rows if "t" in r and "week" in r), key=lambda r: r["t"]):
        groups.setdefault(r["week_resets"], []).append(r)
    tok = rise = 0.0
    spans = []
    for g in groups.values():
        d = g[-1]["week"] - g[0]["week"]
        if d < 5:
            continue
        w = weighted_between(g[0]["t"], g[-1]["t"])
        tok += w; rise += d
        spans.append(dict(hours=round((g[-1]["t"] - g[0]["t"]) / 3600, 1), points=d, weighted_M=round(w / 1e6, 2)))
    if not rise:
        return None
    per = tok / rise / 1e6
    return dict(M_per_week_pct=round(per, 3), week_cap_M=round(per * 100), windows=spans)


def run_prs(repo, start, end):
    q = f"author:phuchai-bot created:{start[:19]}..{end[:19]}"
    out = subprocess.run(["gh", "pr", "list", "-R", repo, "--state", "all", "--limit", "200", "--search", q,
                          "--json", "number,state"], capture_output=True, text=True, timeout=60)
    if out.returncode:
        sys.exit("gh pr list failed: " + out.stderr.strip())
    return {f"{repo}#{d['number']}": d["state"] for d in json.loads(out.stdout)}


def main(argv):
    log = label = repo = None
    if argv[:1] == ["--calibrate"]:
        print(json.dumps(calibrate(argv[1] if len(argv) > 1 else QUOTA_LOG)))
        return
    ids = []
    it = iter(argv)
    for a in it:
        if a == "--log":
            log = next(it)
        elif a == "--repo":
            repo = next(it)
        elif a == "--label":
            label = next(it)
        else:
            ids.append(a)
    if not ids or not repo:
        sys.exit(__doc__)
    loop = dict(calls=0, w=0.0, ctx=[], ts=[])
    workers = []
    for sid in ids:
        p = find(sid)
        s = scan(p)
        loop["calls"] += s["calls"]; loop["w"] += s["w"]; loop["ctx"] += s["ctx"]; loop["ts"] += s["ts"]
        for wp in glob.glob(os.path.join(p[:-6], "subagents", "*.jsonl")):
            ws = scan(wp)
            workers.append(ws)
    ww = sum(x["w"] for x in workers)
    total = loop["w"] + ww
    ts = sorted(loop["ts"])
    states = run_prs(repo, ts[0], ts[-1]) if ts else {}
    merged = sum(1 for v in states.values() if v == "MERGED")
    out = dict(
        label=label, sessions=ids, start=ts[0] if ts else None, end=ts[-1] if ts else None,
        weighted_M=round(total / 1e6, 2), loop_M=round(loop["w"] / 1e6, 2), workers_M=round(ww / 1e6, 2),
        loop_calls=loop["calls"], loop_ctx_start_K=round(loop["ctx"][0] / 1e3) if loop["ctx"] else None,
        loop_ctx_avg_K=round(sum(loop["ctx"]) / len(loop["ctx"]) / 1e3) if loop["ctx"] else None,
        loop_ctx_max_K=round(max(loop["ctx"]) / 1e3) if loop["ctx"] else None,
        workers=len(workers), worker_avg_M=round(ww / len(workers) / 1e6, 3) if workers else None,
        worker_ctx_start_K=round(sum(x["ctx"][0] for x in workers if x["ctx"]) / max(1, len(workers)) / 1e3) if workers else None,
        prs_opened=len(states), prs_merged=merged, prs=states,
        weighted_M_per_merged_pr=round(total / 1e6 / merged, 2) if merged else None,
    )
    cal = calibrate(QUOTA_LOG)
    if cal:
        out["week_pct_est"] = round(total / 1e6 / cal["M_per_week_pct"], 1)
        out["week_cap_M_used"] = cal["week_cap_M"]
    q = quota_used(QUOTA_LOG, ts[0], ts[-1]) if ts else None
    if q:
        out.update(q)
        out["week_pct_per_merged_pr"] = round(q["week_pct"] / merged, 2) if merged else None
    line = json.dumps(out)
    print(line)
    if log:
        with open(log, "a", encoding="utf-8") as f:
            f.write(line + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
