#!/usr/bin/env python3
"""Print this chat's current context size in tokens, read from its own transcript.

Usage: python context_size.py [<session-id>]

With no argument it reads CLAUDE_CODE_SESSION_ID, which Claude Code sets in every
session's shell; pass an id only to measure another chat. The id is the full UUID
(the transcript file name without `.jsonl`), never the six-character ListAgents ID. The size is what the
last model call read: input + cache read + cache creation tokens. Exit code 0 and
one integer on stdout; exit code 2 if the transcript or a usage line is not found.
Used by workflow:self-drive step 7a. Read-only; touches nothing else.
"""
import glob
import json
import os
import sys


def latest_context(path):
    last = None
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            m = o.get("message")
            u = m.get("usage") if isinstance(m, dict) else None
            if u:
                last = (
                    u.get("input_tokens", 0)
                    + u.get("cache_read_input_tokens", 0)
                    + u.get("cache_creation_input_tokens", 0)
                )
    return last


def main():
    if len(sys.argv) > 2:
        print(__doc__, file=sys.stderr)
        return 2
    sid = sys.argv[1] if len(sys.argv) == 2 else os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    if not sid:
        print("no session id: pass one or run inside Claude Code", file=sys.stderr)
        return 2
    pattern = os.path.join(os.path.expanduser("~"), ".claude", "projects", "*", sid + ".jsonl")
    files = glob.glob(pattern)
    if not files:
        print("transcript not found for " + sid, file=sys.stderr)
        return 2
    n = latest_context(files[0])
    if n is None:
        print("no usage line yet", file=sys.stderr)
        return 2
    print(n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
