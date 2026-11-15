"""Dispatcher hook: new checks reach running chats without a plugin reload.

Why: a running chat reads `hooks.json` once, and no agent, script or hook can make it re-read
(standard: findings/claude-code-plugin-reload-running-chat, checked 2026-11-15). But every hook is
a fresh process that runs a script from the plugin's source folder, so an edit to an existing
script takes effect at the chat's next call (tested 2026-11-15, same finding). This one script is
registered once for PreToolUse, UserPromptSubmit and Stop with no matcher; it loads every module
in `hooks/checks/` from disk on each call. A new check is a new file there: no `hooks.json` entry,
no reload. A chat that started before the dispatcher was registered needs one reload or a restart
to get the dispatcher itself, once.

A check module defines:
    EVENTS = {"PreToolUse"}    # optional; default: all three events
    TOOLS = {"ScheduleWakeup"} # optional, PreToolUse only; default: every tool
    def run(payload: dict) -> str | None:   # text to add to the chat's context, or None

Results are joined into one `additionalContext`. A check cannot deny or block (the guards that
refuse keep their own registered hooks, where a missing registration fails loudly); a module that
raises is skipped and logged, so one broken file never traps a turn or silences the others.
Files starting with `_` or `test_` are not loaded. Keep checks fast: they all run in this one
process on every matching call, and a hook timeout drops the whole result.

Guard against a bad edit: it reaches every running chat at the next call, so each check needs a
test (`checks/test_*.py`) before it is pushed.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
import traceback
from pathlib import Path

DEFAULT_EVENTS = {"PreToolUse", "UserPromptSubmit", "Stop"}
CHECKS_DIR = Path(__file__).with_name("checks")
ERROR_LOG = Path.home() / ".claude" / "hook-cache" / "dispatch-errors.log"


def _log_error(name: str, exc: BaseException) -> None:
    try:
        ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
        with ERROR_LOG.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {name}: "
                    f"{''.join(traceback.format_exception_only(type(exc), exc)).strip()}\n")
    except OSError:
        pass


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(f"dispatch_check_{path.stem}", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_checks(payload: dict, checks_dir: Path = CHECKS_DIR) -> list[str]:
    event = str(payload.get("hook_event_name", ""))
    tool = payload.get("tool_name")
    texts: list[str] = []
    if event not in DEFAULT_EVENTS or not checks_dir.is_dir():
        return texts
    for path in sorted(checks_dir.glob("*.py")):
        if path.name.startswith(("_", "test_")):
            continue
        try:
            module = _load(path)
            if module is None:
                continue
            if event not in set(getattr(module, "EVENTS", DEFAULT_EVENTS)):
                continue
            tools = getattr(module, "TOOLS", None)
            if event == "PreToolUse" and tools is not None and tool not in set(tools):
                continue
            text = module.run(payload)
        except Exception as exc:  # one broken check must not trap the turn or hide the others
            _log_error(path.name, exc)
            continue
        if text:
            texts.append(str(text))
    return texts


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return 0
        texts = run_checks(payload)
        event = str(payload.get("hook_event_name", ""))
    except Exception:  # never trap a turn on a bug here
        return 0
    if texts:
        json.dump(
            {"hookSpecificOutput": {"hookEventName": event, "additionalContext": "\n\n".join(texts)}},
            sys.stdout,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
