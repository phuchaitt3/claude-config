"""PreToolUse and PostToolUse hook: keep practice checks (software, research methods, hiring or any other field) in the findings register.

Before a web search or fetch, remind the chat to read `~/claude-config/findings/` first, so a practice
already checked is answered from the register and not searched again. After one, remind it to add or
update the entry and tag the point where it is written. The rule is "Industry practice" in
`rules/working-rules.md`; the tag format is in the `workflow:rule-change` skill, which loads only when a rule
changes, so a chat that checks a practice to answer a question never sees it (user's decision, 2026-10-31,
register added 2026-11-01). A hook cannot tell a register check from any other search, so this one only
reminds, in one line, and never blocks.

Fails open: any error prints nothing and exits 0.
"""

from __future__ import annotations

import json
import sys

BEFORE = (
    "Before searching: if this is about a practice, research result, hiring-market figure or tool behaviour (any field), read `~/claude-config/findings/README.md`. "
    "If an entry covers the question and is under 12 months old, answer from it and cite it instead of "
    "searching. Otherwise ignore this."
)

AFTER = (
    "If this search checked a rule, a documented point or a fact (practice, research, hiring-market data) outside this repository, add or update its entry "
    "in `~/claude-config/findings/` in this turn (finding, source links, limits, date), and tag the point "
    "where it is written: `(standard: findings/<topic>, checked YYYY-MM-DD)`, or `(departs from standard: "
    "<reason>)`. Agents then skip re-checking it for 12 months (`rules/working-rules.md`, \"Industry "
    "practice\"). Otherwise ignore this."
)

TOOLS = ("WebSearch", "WebFetch")
REMINDERS = {"PreToolUse": BEFORE, "PostToolUse": AFTER}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") not in TOOLS:
        return 0
    event = payload.get("hook_event_name")
    if event not in REMINDERS:
        event = "PostToolUse"
    json.dump({"hookSpecificOutput": {
        "hookEventName": event, "additionalContext": REMINDERS[event],
    }}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
