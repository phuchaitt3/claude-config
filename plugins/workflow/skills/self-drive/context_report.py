#!/usr/bin/env python3
"""Summarise the restart-threshold trial from ~/.claude/context-threshold-log.jsonl.

Usage: python context_report.py [<log path>]

The log is written by `context_size.py --log` at the end of every self-drive round
(step 7a). Each session's last line is its fullest record. For each threshold in force
it prints: sessions, handovers, turns, cost per turn, tool-error rate, and the medians
of the starting context F, growth per turn g and restart cost R (cost until the first
Edit/Write). It then evaluates the cost model

    f(T) = r*(F+T)/2 + R*g/(T-F)        (cost per turn, without the constant part)
    T*   = F + sqrt(2*R*g/r)            (the threshold that minimises f)

with r the cache-read weight, from all sessions together. Quality outcomes (PRs merged,
PRs needing a fix-up) are not in the log: join each session's `session_started`..`ts`
window to `gh pr list --state all --author phuchai-bot --json number,createdAt,mergedAt`
when the trial is assessed. Read-only.
"""
import json
import math
import os
import statistics as st
import sys

LOG = os.path.join(os.path.expanduser("~"), ".claude", "context-threshold-log.jsonl")


def load(path):
    last = {}
    handovers = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            last[r["session_id"]] = r
            if r.get("event") == "handover":
                handovers[r["session_id"]] = True
    for sid, r in last.items():
        r["handed_over"] = handovers.get(sid, False)
    return list(last.values())


def growth(r):
    return (r["ctx_max"] - r["ctx_first"]) / max(1, r["turns"] - 1)


def f_of_t(t, F, R, g, w_read):
    return w_read * (F + t) / 2 + R * g / (t - F)


def summarise(recs):
    out = {"sessions": len(recs), "handovers": sum(r["handed_over"] for r in recs)}
    turns = sum(r["turns"] for r in recs)
    calls = sum(r["tool_calls"] for r in recs)
    out["turns"] = turns
    out["cost_per_turn"] = round(sum(r["cost_units"] for r in recs) / max(1, turns))
    out["tool_error_pct"] = round(100 * sum(r["tool_errors"] for r in recs) / max(1, calls), 1)
    out["F"] = round(st.median(r["ctx_first"] for r in recs))
    out["g"] = round(st.median(growth(r) for r in recs))
    rs = [r["cost_to_first_edit"] for r in recs if r.get("cost_to_first_edit")]
    out["R"] = round(st.median(rs)) if rs else None
    return out


def main(argv):
    path = argv[1] if len(argv) > 1 else LOG
    if not os.path.exists(path):
        print("no log yet at " + path, file=sys.stderr)
        return 2
    recs = load(path)
    if not recs:
        print("log is empty", file=sys.stderr)
        return 2
    for t in sorted({r["threshold"] for r in recs}):
        print("threshold", t, json.dumps(summarise([r for r in recs if r["threshold"] == t])))
    s = summarise(recs)
    w_read = recs[-1].get("weights", [0.1])[0]
    if s["R"] and s["g"] > 0:
        t_star = s["F"] + math.sqrt(2 * s["R"] * s["g"] / w_read)
        print("all", json.dumps(s))
        print("T* = %d" % t_star)
        for t in (125000, 150000, 175000, 200000):
            if t > s["F"]:
                print("f(%d) = %d" % (t, f_of_t(t, s["F"], s["R"], s["g"], w_read)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
