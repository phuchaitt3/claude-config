#!/usr/bin/env python3
"""Cost per merged PR for a self-drive run, read from Claude Code transcripts.

Usage: python selfdrive_cost.py --repo OWNER/NAME <session-id> [<successor-id> ...] [--log FILE] [--label TEXT]

Pass the loop chat's session id and any successor chats from a context reset.
Counts each chat plus its subagent workers. Prints one JSON line; --log appends it
to FILE (one run per line) so runs can be compared over time.

"weighted" is an estimate of quota use, in base-input-token units: input x1,
cache write x1.25, cache read x0.1, output x5 (API price ratios; how a subscription
quota is metered is not published). Compare runs with each other, not with the quota.

Read-only, except --log. PRs are those the bot opened in --repo between the run's first
and last model call (`gh pr list`, needs gh signed in); another chat in the same repo
in that window would be counted too, so run one loop per repo.
"""
import glob, json, os, subprocess, sys

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


def run_prs(repo, start, end):
    q = f"author:phuchai-bot created:{start[:19]}..{end[:19]}"
    out = subprocess.run(["gh", "pr", "list", "-R", repo, "--state", "all", "--limit", "200", "--search", q,
                          "--json", "number,state"], capture_output=True, text=True, timeout=60)
    if out.returncode:
        sys.exit("gh pr list failed: " + out.stderr.strip())
    return {f"{repo}#{d['number']}": d["state"] for d in json.loads(out.stdout)}


def main(argv):
    log = label = repo = None
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
    line = json.dumps(out)
    print(line)
    if log:
        with open(log, "a", encoding="utf-8") as f:
            f.write(line + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
