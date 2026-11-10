"""Stop hook: catch a reply that asks the user to act on a PR or issue that is already closed.

The working rules say status comes from `gh` in the same turn, but a written rule relies on the
chat remembering it, and on a long turn the state it read at the start goes stale (a PR the
user merged mid-turn was reported as waiting for their merge, 2026-11-11). This hook enforces
the check at the point of use: when the chat's final message tells the user to act on `#n`
(merge, review, "needs you", "waits for you", "press"), it asks GitHub for that item's state,
and if it is already merged or closed it blocks the stop once, so the chat posts a correction.

Turns with no such line make no `gh` call. A `gh` failure lets the turn end (a guard against a
slip, not a gate). Standard: standards/agent-state-freshness, checked 2026-11-11 (check at the
point of use, cheap and targeted, not by refreshing everything).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

# Phrases that ask the user to act on an item.
_ACTION = re.compile(
    r"needs?[- ]you|needs? your|waits? (?:for|on) (?:you|your)|waiting (?:for|on) (?:you|your)"
    r"|your (?:merge|review|approval)|for your review|press\b|please (?:merge|review|approve)"
    r"|\bto do:|\byou (?:can |could |should )?(?:merge|review|approve)\b",
    re.I,
)
_URL = re.compile(r"github\.com/([\w.-]+/[\w.-]+)/(?:pull|issues)/(\d+)")
_REF = re.compile(r"(?<![\w/])#(\d+)\b")
MAX_ITEMS = 5

# (repo or None for the current one, number) -> (state, merged)
StateFn = Callable[[str | None, int, str], tuple[str, bool]]


def item_state(repo: str | None, number: int, cwd: str) -> tuple[str, bool]:
    """The issue or PR's state ("open" or "closed") and whether it is a merged PR."""
    path = f"repos/{repo or '{owner}/{repo}'}/issues/{number}"
    result = subprocess.run(
        ["gh", "api", path, "--jq", "[.state, (.pull_request.merged_at != null)] | @json"],
        cwd=cwd or ".", capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=15, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"gh exited with {result.returncode}")
    state, merged = json.loads(result.stdout.strip())
    return str(state), bool(merged)


def claimed_items(text: str) -> list[tuple[str | None, int]]:
    """Items the message asks the user to act on: a line with an action phrase and a reference."""
    items: list[tuple[str | None, int]] = []
    for line in text.splitlines():
        if not _ACTION.search(line):
            continue
        linked = [(repo, int(number)) for repo, number in _URL.findall(line)]
        items += linked
        # `[PR #n](.../pull/n)` names the same item twice; keep the URL's, which has the repo.
        items += [
            (None, int(n))
            for n in _REF.findall(_URL.sub("", line))
            if int(n) not in {number for _, number in linked}
        ]
    seen: list[tuple[str | None, int]] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen[:MAX_ITEMS]


def stale(text: str, cwd: str, state: StateFn = item_state) -> list[str]:
    """One line per claimed item that is no longer open."""
    found: list[str] = []
    for repo, number in claimed_items(text):
        try:
            current, merged = state(repo, number, cwd)
        except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired):
            continue
        if current != "open":
            name = f"{repo}#{number}" if repo else f"#{number}"
            found.append(f"{name} is already {'merged' if merged else 'closed'}")
    return found


def last_message(payload: dict) -> str:
    """The chat's final message: from the payload when the harness sends it, else the transcript."""
    text = payload.get("last_assistant_message")
    if isinstance(text, str) and text:
        return text
    path = payload.get("transcript_path")
    if not path:
        return ""
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    for raw in reversed(lines):
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "assistant":
            continue
        content = (entry.get("message") or {}).get("content")
        if isinstance(content, str):
            return content
        texts = [c.get("text", "") for c in content or [] if c.get("type") == "text"]
        if texts:
            return "\n".join(texts)
    return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict) or payload.get("stop_hook_active"):
        return 0  # one correction per turn; never loop
    try:
        found = stale(last_message(payload), str(payload.get("cwd") or "."), item_state)
    except Exception:  # a guard against a slip: never trap the turn on a bug
        return 0
    if found:
        json.dump(
            {
                "decision": "block",
                "reason": (
                    "Your reply asks the user to act on items that have changed: "
                    + "; ".join(found)
                    + ". Check them with gh now and post a short correction (working rules, "
                    "'Status comes from gh in the same turn')."
                ),
            },
            sys.stdout,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
