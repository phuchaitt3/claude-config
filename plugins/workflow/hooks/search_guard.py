"""PreToolUse hook: refuse a whole-drive search from a shell command.

`find /`, `find C:\\`, `grep -r pattern /d` and `Get-ChildItem C:\\ -Recurse` walk every file on the
machine. Under Git Bash on Windows they take hours; if the shell call times out, the search keeps
running as an orphan and holds CPU and disk (two `find /` processes ran 5-6 hours and made a shared
laptop lag). The agent's own Glob and Grep tools, or a search scoped to a project folder, answer the
same questions. Fails open: it guards a known mistake and is not a security boundary (standard:
findings/agent-process-and-resource-control, checked 2026-11-12; findings/agent-permission-enforcement,
checked 2026-11-05).
"""

from __future__ import annotations

import json
import re
import shlex
import sys

# A path that is a whole drive or the whole filesystem: `/`, `/c`, `/d/`, `/mnt/c`, `C:`, `C:\`, `C:/`, `~`.
_ROOT = re.compile(r"^(?:/|/[a-zA-Z]|/mnt/[a-zA-Z]|[a-zA-Z]:|~|\$HOME)[/\\]*$")
_SEARCHERS = {"find", "grep", "egrep", "fgrep", "rg", "ag", "fd", "locate"}
_GCI = {"get-childitem", "gci", "ls", "dir"}
_SEPARATORS = {";", "&&", "||", "|", "&"}

_MESSAGE = (
    "Refused: `{cmd}` searches a whole drive. Under Git Bash this runs for hours and survives a timed-out "
    "call as an orphan that keeps the CPU busy. Use the Glob or Grep tool, or scope the command to a "
    "project folder (for example `find ./src ...`). To locate an installed Python package, run "
    "`python -c \"import <pkg>; print(<pkg>.__file__)\"`. Any search that must stay broad gets "
    "`timeout 60` in front of it."
)


def _segments(command: str) -> list[list[str]]:
    try:
        lexer = shlex.shlex(command, posix=False, punctuation_chars=";&|")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token in _SEPARATORS or set(token) <= set(";&|"):
            segments.append([])
        else:
            segments[-1].append(token)
    return [s for s in segments if s]


def _strip_wrappers(words: list[str]) -> list[str]:
    """Drop a leading `timeout N`, `nice`, `time`, `sudo`, `env` so the real command is first."""
    while words:
        head = words[0].lower()
        if head in {"nice", "time", "sudo", "command", "nohup", "env"}:
            words = words[1:]
        elif head == "timeout":
            words = words[1:]
            while words and (words[0].startswith("-") or re.fullmatch(r"\d+[smhd]?", words[0])):
                words = words[1:]
        else:
            break
    return words


def _is_root(path: str) -> bool:
    return bool(_ROOT.match(path.strip("\"'")))


def refusal(command: str) -> str:
    for words in _segments(command):
        words = _strip_wrappers(words)
        if not words:
            continue
        name = words[0].replace("\\", "/").rsplit("/", 1)[-1].lower().removesuffix(".exe")
        args = words[1:]
        if name == "find":
            # find's start paths come before the first expression token.
            paths = []
            for arg in args:
                if arg.startswith(("-", "(", "!")) and arg != "-":
                    break
                paths.append(arg)
            if any(_is_root(p) for p in paths):
                return _MESSAGE.format(cmd=" ".join(words)[:80])
        elif name in _SEARCHERS - {"find"}:
            recursive = name in {"rg", "ag", "fd", "locate"} or any(
                a.startswith("-") and not a.startswith("--") and ("r" in a or "R" in a) for a in args
            ) or "--recursive" in args
            positional = [a for a in args if not a.startswith("-")]
            if recursive and positional and _is_root(positional[-1]):
                return _MESSAGE.format(cmd=" ".join(words)[:80])
        elif name in _GCI:
            lowered = [a.lower() for a in args]
            recurse = any(a in {"-recurse", "-r", "/s"} or a.startswith("-rec") for a in lowered)
            paths = [a for a in args if not a.startswith("-") and not a.startswith("/s")]
            if recurse and any(_is_root(p) for p in paths):
                return _MESSAGE.format(cmd=" ".join(words)[:80])
    return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") not in ("Bash", "PowerShell"):
        return 0
    tool_input = payload.get("tool_input")
    command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
    try:
        reason = refusal(command)
    except Exception:  # never block on a bug in the guard itself
        return 0
    if reason:
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
