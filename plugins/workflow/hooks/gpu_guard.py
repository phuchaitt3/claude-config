"""PreToolUse hook: refuse a GPU container start outside the machine-wide GPU lock.

A GPU container (`docker run --gpus ...`, `docker compose up` of a file with a GPU service) keeps the
laptop GPU after its start command returns. Started bare, it holds GPU memory that no lock records:
on 2026-11-13 an unnamed `docker run --rm --gpus all` reranker sat idle beside a second copy and an
Ollama model, filling 5.5 of 6 GB. The rule (working-rules, "Laptop GPU") says a GPU service starts
through `gpu_run.py hold`, which keeps the lock until its containers stop, and that a `docker run`
GPU container carries a `--name` or `--label` naming its task so it can be traced.

This hook refuses:
- a GPU container start whose command does not go through `gpu_run.py hold` or `gpu_run.py run`;
- a `docker run --gpus` with neither `--name` nor `--label`.

It reads command text only, so it is a guardrail against mistakes, not a security boundary, and it
fails open on anything it cannot parse or read (standard: findings/shared-gpu-one-machine, checked
2026-11-13; findings/agent-permission-enforcement, checked 2026-11-05).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

_SEPARATORS = {";", "&&", "||", "|", "&"}
_GUARDED = re.compile(r"gpu_run\.py[\"']?\s+(?:hold|run)\b")
_GPU_IN_COMPOSE = re.compile(
    r"capabilities:\s*\[[^\]]*gpu|driver:\s*[\"']?nvidia|runtime:\s*[\"']?nvidia|^\s*gpus:", re.IGNORECASE | re.MULTILINE
)
_DEFAULT_COMPOSE = ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml")

_UNGUARDED = (
    "Refused: `{cmd}` starts a GPU container outside the machine-wide GPU lock. Run it as "
    "`python ~/claude-config/scripts/gpu_run.py hold --wait --purpose <task> -- <command>` in the "
    "background: it holds the lock until the containers stop, and stopping them releases it. Stop the "
    "containers when the task no longer needs them. (Rule: working-rules, \"Laptop GPU\".)"
)
_UNNAMED = (
    "Refused: `{cmd}` starts an unnamed GPU container. Add `--name <task>-<service>` or "
    "`--label gpu-guard.task=<task>` so it can be traced to the task that started it, and stop it when "
    "the task is done. (Rule: working-rules, \"Laptop GPU\".)"
)


def _segments(command: str) -> list[list[str]]:
    try:
        lexer = shlex.shlex(command, posix=False, punctuation_chars=";&|")  # keeps Windows backslashes
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()
    segments: list[list[str]] = [[]]
    for token in tokens:
        token = token.strip("\"'")
        if token in _SEPARATORS or (token and set(token) <= set(";&|")):
            segments.append([])
        else:
            segments[-1].append(token)
    return [s for s in segments if s]


def _name(word: str) -> str:
    return word.replace("\\", "/").rsplit("/", 1)[-1].lower().removesuffix(".exe")


def _strip_wrappers(words: list[str]) -> list[str]:
    while words and words[0].lower() in {"nice", "time", "sudo", "command", "nohup", "env", "&"}:
        words = words[1:]
    while words and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", words[0]):  # VAR=value prefix
        words = words[1:]
    return words


def _docker_run_gpu(args: list[str]) -> tuple[bool, bool]:
    """(requests a GPU, has a name or label) for the arguments after `docker run`."""
    gpu = named = False
    for i, a in enumerate(args):
        low = a.lower()
        value = args[i + 1].lower() if i + 1 < len(args) else ""
        if low == "--gpus" or low.startswith("--gpus="):
            gpu = True
        elif low.startswith("--device") and "nvidia" in f"{low} {value}":
            gpu = True
        elif low in {"--name", "--label", "-l"} or low.startswith(("--name=", "--label=")):
            named = True
        elif not a.startswith("-") and i > 0 and not args[i - 1].startswith("-"):
            break  # the image: options end here
    return gpu, named


def _compose_files(args: list[str], cwd: Path) -> list[Path]:
    files, project_dir = [], cwd
    for i, a in enumerate(args):
        nxt = args[i + 1] if i + 1 < len(args) else ""
        if a in {"-f", "--file"} and nxt:
            files.append(nxt)
        elif a.startswith("--file="):
            files.append(a.split("=", 1)[1])
        elif a == "--project-directory" and nxt:
            project_dir = cwd / nxt
    if files:
        return [cwd / f for f in files]
    return [project_dir / f for f in _DEFAULT_COMPOSE if (project_dir / f).is_file()]


def _compose_up_gpu(args: list[str], cwd: Path) -> bool:
    if "up" not in args:
        return False
    for f in _compose_files(args, cwd):
        try:
            if _GPU_IN_COMPOSE.search(f.read_text(encoding="utf-8", errors="replace")):
                return True
        except OSError:
            continue
    return False


def refusal(command: str, cwd: str) -> str:
    guarded = bool(_GUARDED.search(command))
    here = Path(cwd or os.getcwd())
    for words in _segments(command):
        words = _strip_wrappers(words)
        if not words:
            continue
        head = _name(words[0])
        if head in {"cd", "set-location", "pushd", "sl"} and len(words) > 1:
            target = Path(os.path.expanduser(words[1].strip("\"'")))
            here = target if target.is_absolute() else here / target
            continue
        # A wrapper (`gpu_run.py hold -- docker run ...`, `timeout 60 docker ...`) puts docker later.
        starts = [i for i, w in enumerate(words) if _name(w) in {"docker", "docker-compose"}]
        if not starts:
            continue
        words = words[starts[0]:]
        head = _name(words[0])
        shown = " ".join(words)[:100]
        if head == "docker" and len(words) > 1:
            rest = words[1:]
            if rest[0] == "container" and len(rest) > 1:
                rest = rest[1:]
            if rest[0] == "run":
                gpu, named = _docker_run_gpu(rest[1:])
                if gpu and not guarded:
                    return _UNGUARDED.format(cmd=shown)
                if gpu and not named:
                    return _UNNAMED.format(cmd=shown)
            elif rest[0] == "compose" and not guarded and _compose_up_gpu(rest[1:], here):
                return _UNGUARDED.format(cmd=shown)
        elif head == "docker-compose" and not guarded and _compose_up_gpu(words[1:], here):
            return _UNGUARDED.format(cmd=shown)
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
    if "docker" not in command:
        return 0
    try:
        reason = refusal(command, str(payload.get("cwd") or ""))
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
