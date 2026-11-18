"""Check: remind a chat to smoke-test before a long run (user's decision, 2026-11-18, global scope).

Runs before a Bash or PowerShell call whose command carries `# estimate: N` with N over 5 minutes and
no `# smoke:` tag. It adds one line: run the same command in a short form that exercises every step
end to end (a `--smoke` flag, seconds, nothing logged as a result), fix what it shows, then start
the real run, and tag the real run `# smoke: <what ran>` (or `# smoke: none (<reason>)` for a job
with no short form). A command that is itself a smoke run (`--smoke`, or a short `# estimate`) is
left alone. Reminder only: it never blocks, so a job with no short form is not stopped.
Why: a 10-minute heat run failed on a wrong task name that a 15-second run would have shown.
"""

import json
import re

EVENTS = {"PreToolUse"}
TOOLS = {"Bash", "PowerShell"}
THRESHOLD_MIN = 5.0
_ESTIMATE = re.compile(r"#\s*estimate:\s*(\d+(?:\.\d+)?)\s*(s|sec|m|min|h|hr)?(?![A-Za-z])", re.I)
_SMOKE_TAG = re.compile(r"#\s*smoke:", re.I)


def _minutes(command: str):
    found = _ESTIMATE.findall(command)
    if not found:
        return None
    value, unit = found[-1]
    n = float(value)
    unit = unit.lower()
    return n / 60 if unit in ("s", "sec") else n * 60 if unit in ("h", "hr") else n


def run(payload):
    command = str((payload.get("tool_input") or {}).get("command", ""))
    minutes = _minutes(command)
    if minutes is None or minutes <= THRESHOLD_MIN or _SMOKE_TAG.search(command) or "--smoke" in command:
        return None
    return (f"smoke-test: this run is estimated at {minutes:g} min. Before it, run the same command in a short "
            f"form that exercises every step end to end (a `--smoke` flag, seconds, nothing logged as a result) "
            f"and fix what it shows; unit tests of the parts do not count. Then start the real run tagged "
            f"`# smoke: <what ran>`, or `# smoke: none (<reason>)` for a job with no short form.")
