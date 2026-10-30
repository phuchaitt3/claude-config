"""SessionStart hook: fast-forward ~/claude-config so this machine sees the latest rules and plugin.

The plugin (and the rules file) are read from the ~/claude-config checkout. Changes made on another
machine only arrive after a `git pull` there, so this does it quietly at session start. Safe by
construction: `--ff-only` never merges or rewrites, a dirty or diverged checkout simply fails, and
every failure is silent (offline, no git, a slow network). At most one pull per 30 minutes, so a
`/clear` or a resume does not repeat it. Plugin auto-update then picks up a newer plugin version
at the following startup.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = Path.home() / "claude-config"
STAMP = Path.home() / ".claude" / "hook-cache" / "pull_config.stamp"
MIN_INTERVAL_S = 30 * 60
TIMEOUT_S = 8


def due(now: float, stamp: Path = STAMP, interval: float = MIN_INTERVAL_S) -> bool:
    try:
        return now - stamp.stat().st_mtime >= interval
    except OSError:
        return True


def pull(repo: Path = REPO) -> bool:
    if not (repo / ".git").exists():
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), "pull", "--ff-only", "--quiet"],
            capture_output=True, text=True, timeout=TIMEOUT_S, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def main() -> int:
    if not due(time.time()):
        return 0
    STAMP.parent.mkdir(parents=True, exist_ok=True)
    STAMP.touch()  # stamp first: a slow or failing pull must not be retried on every session
    pull()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # a broken hook must never get in the way of a session
        sys.exit(0)
