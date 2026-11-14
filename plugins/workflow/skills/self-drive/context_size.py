#!/usr/bin/env python3
"""Print this chat's current context size in tokens, read from its own transcript.

Usage: python context_size.py [--log] [--threshold N] [<session-id>]

With no session id it reads CLAUDE_CODE_SESSION_ID, which Claude Code sets in every
session's shell; pass an id only to measure another chat. The id is the full UUID
(the transcript file name without `.jsonl`), never the six-character ListAgents ID. The size is what the
last model call read: input + cache read + cache creation tokens. Exit code 0 and
one integer on stdout; exit code 2 if the transcript or a usage line is not found.

--log appends one JSON line of session statistics to ~/.claude/context-threshold-log.jsonl
(local, never committed), for the restart-threshold trial (self-drive step 7a); the
transcripts themselves are deleted after 30 days, so the log keeps what the analysis
needs. --threshold names the restart threshold in force (default 150000), recorded in
the line and used to mark it as a handover. `context_report.py` reads the log.
Used by workflow:self-drive step 7a. Writes nothing except the log line.
"""
import argparse
import glob
import json
import os
import sys
import time

DEFAULT_THRESHOLD = 150000
LOG = os.path.join(os.path.expanduser("~"), ".claude", "context-threshold-log.jsonl")
QUOTA = os.path.join(os.path.expanduser("~"), ".claude", "hook-cache", "quota.json")
# Relative cost weights, in units of the input-token price: cache read, 1-hour cache write, output.
W_READ, W_WRITE, W_OUT = 0.1, 2.0, 5.0


def read_turns(path):
    """Model calls of the main thread, merged by request id, in order, plus tool error ids."""
    turns, order, errors = {}, [], set()
    first_ts = None
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            if not isinstance(o, dict):
                continue
            if first_ts is None and o.get("timestamp"):
                first_ts = o["timestamp"]
            m = o.get("message")
            if not isinstance(m, dict):
                continue
            c = m.get("content")
            if o.get("type") == "user" and isinstance(c, list):
                for x in c:
                    if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("is_error"):
                        errors.add(x.get("tool_use_id"))
            u = m.get("usage")
            if o.get("type") != "assistant" or o.get("isSidechain") or not u:
                continue
            key = o.get("requestId") or m.get("id") or str(len(order))
            if key not in turns:
                order.append(key)
                turns[key] = {"ctx": 0, "out": 0, "read": 0, "write": 0, "tools": []}
            t = turns[key]
            ctx = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            t["ctx"] = max(t["ctx"], ctx)
            t["out"] = max(t["out"], u.get("output_tokens", 0))
            t["read"] = max(t["read"], u.get("cache_read_input_tokens", 0))
            t["write"] = max(t["write"], u.get("cache_creation_input_tokens", 0))
            if isinstance(c, list):
                t["tools"] += [(x.get("id"), x.get("name")) for x in c if isinstance(x, dict) and x.get("type") == "tool_use"]
    return [turns[k] for k in order], errors, first_ts


def cost(t):
    return t["read"] * W_READ + t["write"] * W_WRITE + t["out"] * W_OUT


def stats(turns, errors):
    """Statistics the threshold analysis needs; context_report.py says how they are used."""
    calls = [tid for t in turns for tid, _ in t["tools"]]
    compactions = sum(1 for a, b in zip(turns, turns[1:]) if b["ctx"] < a["ctx"] * 0.6)
    first_edit = next((i for i, t in enumerate(turns) if any(n in ("Edit", "Write") for _, n in t["tools"])), None)
    bins = {}
    for t in turns:
        b = str(int(t["ctx"] // 50000) * 50)  # "50" means 50k-100k
        s = bins.setdefault(b, {"turns": 0, "calls": 0, "errors": 0, "cost": 0.0})
        s["turns"] += 1
        s["calls"] += len(t["tools"])
        s["errors"] += sum(1 for tid, _ in t["tools"] if tid in errors)
        s["cost"] = round(s["cost"] + cost(t), 1)
    return {
        "turns": len(turns),
        "ctx_first": turns[0]["ctx"],
        "ctx_max": max(t["ctx"] for t in turns),
        "tool_calls": len(calls),
        "tool_errors": sum(1 for c in calls if c in errors),
        "cost_units": round(sum(cost(t) for t in turns), 1),
        "output_tokens": sum(t["out"] for t in turns),
        "turns_to_first_edit": first_edit,
        "cost_to_first_edit": round(sum(cost(t) for t in turns[:first_edit]), 1) if first_edit is not None else None,
        "compactions": compactions,
        "by_ctx_bin": bins,
    }


def quota():
    try:
        with open(QUOTA, encoding="utf-8") as f:
            q = json.load(f)
        rl = q.get("rate_limits", {})
        return {
            "quota_written_at": q.get("written_at"),
            "five_hour_pct": rl.get("five_hour", {}).get("used_percentage"),
            "five_hour_resets_at": rl.get("five_hour", {}).get("resets_at"),
            "seven_day_pct": rl.get("seven_day", {}).get("used_percentage"),
        }
    except (OSError, ValueError, AttributeError):
        return {}


def record(sid, path, turns, errors, first_ts, threshold):
    now_ctx = turns[-1]["ctx"]
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session_id": sid,
        "project": os.path.basename(os.path.dirname(path)),
        "session_started": first_ts,
        "threshold": threshold,
        "ctx_now": now_ctx,
        "event": "handover" if now_ctx > threshold else "round",
        "weights": [W_READ, W_WRITE, W_OUT],
    }
    rec.update(stats(turns, errors))
    rec.update(quota())
    return rec


def main(argv=None):
    p = argparse.ArgumentParser(description="Print this chat's context size; --log records session statistics.")
    p.add_argument("session_id", nargs="?")
    p.add_argument("--log", action="store_true")
    p.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    a = p.parse_args(argv)
    sid = a.session_id or os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if not sid:
        print("no session id: pass one or run inside Claude Code", file=sys.stderr)
        return 2
    pattern = os.path.join(os.path.expanduser("~"), ".claude", "projects", "*", sid + ".jsonl")
    files = glob.glob(pattern)
    if not files:
        print("transcript not found for " + sid, file=sys.stderr)
        return 2
    turns, errors, first_ts = read_turns(files[0])
    if not turns:
        print("no usage line yet", file=sys.stderr)
        return 2
    print(turns[-1]["ctx"])
    if a.log:
        try:
            os.makedirs(os.path.dirname(LOG), exist_ok=True)
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(record(sid, files[0], turns, errors, first_ts, a.threshold)) + "\n")
        except OSError as e:
            print("log not written: " + str(e), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
