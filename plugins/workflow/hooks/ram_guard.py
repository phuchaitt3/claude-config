"""PreToolUse hook: refuse a full test run or a build outside the machine-wide RAM lock.

The working rules ("Heavy RAM/CPU jobs") say a full test suite, a build, or a load of a large model
or dataset into system RAM goes through `gpu_run.py run --resource ram`, so two chats never run one
at once on the 16 GB laptop. That was text only, and on 2026-11-15 an agent ran a 537-test suite
bare (user's decision, 2026-11-15: refuse unguarded, as `gpu_guard` does for GPU containers).

Refused unless the command goes through `gpu_run.py run` or `hold` (a GPU `run`/`hold` takes the RAM
lock first since 2026-11-17, so any of them covers RAM):
- a full test run: `pytest` (also `python -m pytest`, `uv run pytest`, `poetry run pytest`) with no
  test file or `::node` target, and `npm|pnpm|yarn test`;
- a build: `npm|pnpm|yarn [run] build*`, `next build`, `docker build`, `docker buildx build`,
  `docker compose build`, `docker-compose build`;
- a Compose stack: `docker compose ... up` / `docker-compose up`. A detached one (`-d`, `--detach`,
  `--wait`) keeps its memory after the command returns, so only `gpu_run.py hold` (which keeps the lock
  until the stack stops) covers it; `run` would release at once (user's decision, 2026-11-17, after a
  stack held RAM between another loop's model loads overnight; standard: findings/shared-gpu-one-machine
  and findings/memory-admission-one-machine, checked 2026-11-13 and 2026-11-17).
A single test file, linters, type checks and git pass. A large model or dataset load inside a script
is invisible here and stays the agent's judgement.

It reads command text only: a guardrail against mistakes, not a security boundary. It fails open on
anything it cannot parse (standard: findings/agent-process-and-resource-control, checked 2026-11-12).
"""

from __future__ import annotations

import json
import re
import sys

from gpu_guard import _compose_subcommand, _detached, _name, _segments, _strip_wrappers

_GUARDED = re.compile(r"gpu_run\.py[\"']?\s+(?:run|hold)\b")
_HELD = re.compile(r"gpu_run\.py[\"']?\s+hold\b")
_RUNNERS = {"uv", "poetry", "pipenv", "pdm", "hatch", "rye"}  # `<runner> run <cmd>`
_PKG = {"npm", "pnpm", "yarn"}

_REFUSED = (
    "Refused: `{cmd}` is a {kind} outside the machine-wide RAM lock, so another chat's heavy job "
    "could run beside it on the 16 GB laptop. Run it as "
    "`python ~/claude-config/scripts/gpu_run.py run --resource ram --wait -- {cmd}` (the lock is "
    "immediate when free; a GPU job goes inside it). A single test file needs no lock. "
    "(Rule: working-rules, \"Heavy RAM/CPU jobs\".)"
)

_REFUSED_STACK = (
    "Refused: `{cmd}` starts a Docker Compose stack, which keeps its memory after the command returns, "
    "outside the machine-wide RAM lock. Start it in the background as "
    "`python ~/claude-config/scripts/gpu_run.py hold --resource ram --wait --purpose <task> -- {cmd}` "
    "(a stack with a GPU service: leave out `--resource ram`, and it holds both locks). The lock is "
    "released when the stack stops (`docker compose down`). "
    "(Rule: working-rules, \"Heavy RAM/CPU jobs\".)"
)


def _unwrap(words: list[str]) -> list[str]:
    """Drop `uv run`, `python -m` and similar so the real program comes first."""
    while words:
        head = _name(words[0])
        if head in _RUNNERS and len(words) > 1 and words[1] == "run":
            words = [w for w in words[2:]]
            while words and words[0].startswith("-"):  # `uv run --frozen pytest`
                words = words[1:]
        elif re.fullmatch(r"python[0-9.]*|py", head) and len(words) > 2 and words[1] == "-m":
            words = words[2:]
        else:
            return words
    return words


_PYTEST_VALUE_OPTS = {"-k", "-m", "-p", "-c", "-o", "--rootdir", "--maxfail", "--tb", "-n",
                      "--durations", "--junitxml", "--basetemp", "--ignore", "--deselect", "-W"}


def _full_pytest(args: list[str]) -> bool:
    """True when no argument names a test file or node (`x.py`, `x.py::test`)."""
    skip = False
    for a in args:
        if skip:
            skip = False
        elif a in _PYTEST_VALUE_OPTS:
            skip = True
        elif a.startswith("-"):
            continue
        elif "::" in a or a.endswith(".py"):
            return False
    return True


def kind_of(words: list[str]) -> str:
    """'full test run', 'build', 'stack' (detached compose up), 'stack in foreground' or ''."""
    if any(_name(w) == "gpu_run.py" for w in words) and "--" in words:  # a wrapper: check its command
        words = words[words.index("--") + 1:]
    words = _unwrap(_strip_wrappers(words))
    if not words:
        return ""
    head, rest = _name(words[0]), words[1:]
    if head in {"pytest", "py.test"}:
        return "full test run" if _full_pytest(rest) else ""
    if head in _PKG and rest:
        sub = rest[1] if rest[0] == "run" and len(rest) > 1 else rest[0]
        if sub == "test" or sub.startswith("test:"):
            return "full test run"
        if sub == "build" or sub.startswith("build:"):
            return "build"
        return ""
    if head == "next" and rest[:1] == ["build"]:
        return "build"
    if head == "docker" and rest:
        if rest[0] == "build" or rest[:2] == ["buildx", "build"] or rest[:2] == ["image", "build"]:
            return "build"
        if rest[0] == "compose":
            sub, after = _compose_subcommand(rest[1:])
            if sub == "up":
                return "stack" if _detached(after) else "stack in foreground"
            if "build" in rest[1:]:
                return "build"
    if head == "docker-compose":
        sub, after = _compose_subcommand(rest)
        if sub == "up":
            return "stack" if _detached(after) else "stack in foreground"
        if "build" in rest:
            return "build"
    return ""


def _inner(words: list[str]) -> str:
    """The wrapped command of `gpu_run.py ... -- <command>`, else the whole segment."""
    if any(_name(w) == "gpu_run.py" for w in words) and "--" in words:
        words = words[words.index("--") + 1:]
    return " ".join(words)[:120]


def refusal(command: str) -> str:
    for words in _segments(command):
        kind = kind_of(words)
        text = " ".join(words)
        if kind == "stack" and not _HELD.search(text):  # `run` would release while the stack runs
            return _REFUSED_STACK.format(cmd=_inner(words))
        if kind and kind != "stack" and not _GUARDED.search(text):
            template = _REFUSED_STACK if kind.startswith("stack") else _REFUSED
            return template.format(cmd=_inner(words), kind=kind)
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
    if not re.search(r"pytest|py\.test|\btest\b|build|\bup\b", command):
        return 0
    try:
        reason = refusal(command)
    except Exception:  # noqa: BLE001 (never block on a bug in the guard itself)
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
