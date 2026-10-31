"""PostToolUse hook: after a web search or fetch, remind the chat to tag a checked practice.

The tag rule ("Industry-standard tags") lives in the `workflow:rule-change` skill, which loads only when
a rule changes. A chat that checks a practice to answer a question, or to write a doc, never sees it, and
the next chat checks the same practice again (user's decision, 2026-10-31). A hook cannot tell a
standards check from any other search, so this one only reminds, in one line, and never blocks.

Fails open: any error prints nothing and exits 0.
"""

from __future__ import annotations

import json
import sys

REMINDER = (
    "If this search checked a rule or a documented point against industry practice, tag that point where "
    "it is written: `(standard: <source>, checked YYYY-MM-DD)`, or `(departs from standard: <reason>)`. "
    "Agents then skip re-checking it for 12 months (`workflow:rule-change`, \"Industry-standard tags\"). "
    "Otherwise ignore this."
)

TOOLS = ("WebSearch", "WebFetch")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") not in TOOLS:
        return 0
    json.dump({"hookSpecificOutput": {
        "hookEventName": "PostToolUse", "additionalContext": REMINDER,
    }}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
