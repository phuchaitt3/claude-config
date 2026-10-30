"""Merge the per-machine Claude settings this repo needs into ~/.claude/settings.json.

Idempotent and additive: it registers the `personal-config` marketplace (a directory source
pointing at the claude-config checkout) with autoUpdate on, and enables `workflow@personal-config`.
It never removes or changes anything else. The old file is copied to settings.json.bak-<date>
first. Prints what it changed (or "no change").

    python merge_settings.py [--settings PATH] [--repo PATH]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKETPLACE = "personal-config"
PLUGIN = "workflow@personal-config"


def merge(settings: dict, repo: str) -> list[str]:
    """Apply the needed entries to `settings` in place; return a description of each change."""
    changes: list[str] = []
    markets = settings.setdefault("extraKnownMarketplaces", {})
    entry = markets.setdefault(MARKETPLACE, {})
    if entry.get("source") != {"source": "directory", "path": repo}:
        entry["source"] = {"source": "directory", "path": repo}
        changes.append(f"marketplace {MARKETPLACE} -> {repo}")
    if entry.get("autoUpdate") is not True:
        entry["autoUpdate"] = True
        changes.append("autoUpdate on")
    plugins = settings.setdefault("enabledPlugins", {})
    if plugins.get(PLUGIN) is not True:
        plugins[PLUGIN] = True
        changes.append(f"enabled {PLUGIN}")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", default=str(Path.home() / ".claude" / "settings.json"))
    parser.add_argument("--repo", default=str(Path.home() / "claude-config"))
    args = parser.parse_args()
    path = Path(args.settings)
    if path.exists():
        try:
            settings = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            print(f"{path} is not valid JSON ({exc}); left untouched", file=sys.stderr)
            return 1
    else:
        settings = {}
    changes = merge(settings, args.repo)
    if not changes:
        print("settings: no change")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_name(f"{path.name}.bak-{datetime.now():%Y%m%d-%H%M%S}"))
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("settings: " + "; ".join(changes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
