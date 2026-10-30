"""Claude Code status line: model name and how full the context window is.

Claude Code pipes a JSON object to stdin on each update; `context_window.used_percentage` is the
share of the window in use. The percentage is coloured green under 50, yellow from 50 to 79 and red
from 80, so the user can see when to run /compact or /clear (working rules, "Context"). Prints
nothing if the input is missing or malformed: a status line must never get in the way.
"""

from __future__ import annotations

import json
import sys

GREEN, YELLOW, RED, RESET = "\033[32m", "\033[33m", "\033[31m", "\033[0m"


def colour(percent: float) -> str:
    if percent >= 80:
        return RED
    if percent >= 50:
        return YELLOW
    return GREEN


def render(data: dict) -> str:
    model = (data.get("model") or {}).get("display_name") or ""
    percent = (data.get("context_window") or {}).get("used_percentage")
    parts = [model] if model else []
    if isinstance(percent, (int, float)):
        parts.append(f"{colour(percent)}ctx {percent:.0f}%{RESET}")
    return " | ".join(parts)


def main() -> int:
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            return 0
        line = render(data)
    except (ValueError, OSError):
        return 0
    if line:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
