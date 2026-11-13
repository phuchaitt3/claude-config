"""PreToolUse hook: refuse a GPU container start outside the machine-wide GPU lock.

A GPU container (`docker run --gpus ...`, `docker compose up` of a file with a GPU service) keeps the
laptop GPU after its start command returns. Started bare, it holds GPU memory that no lock records:
on 2026-11-13 an unnamed `docker run --rm --gpus all` reranker sat idle beside a second copy and an
Ollama model, filling 5.5 of 6 GB. The rule (working-rules, "Laptop GPU") says a GPU service starts
through `gpu_run.py hold`, which keeps the lock until its containers stop, and that a `docker run`
GPU container carries a `--name` or `--label` naming its task so it can be traced.

This hook refuses:
- a GPU container start whose command does not go through `gpu_run.py hold` or `gpu_run.py run`;
- a `docker run --gpus` with neither `--name` nor `--label`;
- `timeout` (or `gtimeout`) around a foreground `docker run`, `docker compose run` or `docker compose
  up`, GPU or not. Killing the docker client does not stop the container, and `--rm` never fires
  because the container never exits; on Windows every timeout kills the client outright. The orphan
  that started this hook came from `timeout 280 docker run --rm --gpus all ...` (standard:
  findings/docker-run-timeout-cleanup, checked 2026-11-13; user's decision, 2026-11-13).

Closed 2026-11-13 (user's decision): option parsing of `docker run` stops at the image, so a program's
own `-d` or `--gpus` is not read as a docker option; `docker start` and `docker restart` of an existing
container are refused when `docker inspect` shows it requests a GPU; `docker compose up` is refused only
when the services it starts (named ones plus their `depends_on`, files merged in order) request a GPU, so
a CPU-only service beside a GPU one starts freely. Without PyYAML it falls back to "the file mentions a GPU".

It reads command text only, so it is a guardrail against mistakes, not a security boundary, and it
fails open on anything it cannot parse or read (standard: findings/shared-gpu-one-machine, checked
2026-11-13; findings/agent-permission-enforcement, checked 2026-11-05).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
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
_TIMEOUT = (
    "Refused: `{cmd}` puts a time limit on the docker client, not the container. Killing the client "
    "leaves the container running (and `--rm` never fires), so it keeps its memory and GPU. Instead: "
    "start it detached and named (`docker run -d --name <task>-<what> ...`), wait with your own "
    "deadline (`docker wait <name>` or poll `docker ps`), and `docker stop <name>` in a finally step. "
    "For a GPU container, `gpu_run.py hold --max-minutes N -- docker run -d --name ...` does all of "
    "this and stops it at the deadline. (findings/docker-run-timeout-cleanup)"
)
_TIMEOUTS = {"timeout", "gtimeout"}
_COMPOSE_VALUE_OPTS = {"-f", "--file", "-p", "--project-name", "--project-directory", "--profile",
                       "--env-file", "--ansi", "--parallel", "--progress"}


def _compose_subcommand(args: list[str]) -> tuple[str, list[str]]:
    """('up', [args after it]) for `compose -f x up -d ...`; ('', []) when none is found."""
    skip = False
    for i, a in enumerate(args):
        if skip:
            skip = False
        elif a in _COMPOSE_VALUE_OPTS:
            skip = True
        elif not a.startswith("-"):
            return a, args[i + 1:]
    return "", []


def _detached(args: list[str]) -> bool:
    """True when `-d`/`--detach`/`--wait` is an option of compose `up` (not an argument of a program)."""
    return any(a in {"-d", "--detach", "--wait"} or (a.startswith("-") and not a.startswith("--")
                                                      and "d" in a[1:] and len(a) <= 4) for a in args)


# `docker run` options that take a value; any other `--x` is a flag. Short options that take one:
_RUN_VALUE_OPTS = {
    "--add-host", "--annotation", "--attach", "--blkio-weight", "--cap-add", "--cap-drop", "--cgroup-parent",
    "--cidfile", "--cpu-shares", "--cpus", "--cpuset-cpus", "--detach-keys", "--device", "--dns", "--domainname",
    "--entrypoint", "--env", "--env-file", "--expose", "--group-add", "--gpus", "--health-cmd", "--hostname",
    "--ip", "--ipc", "--label", "--label-file", "--link", "--log-driver", "--log-opt", "--mac-address",
    "--memory", "--memory-swap", "--mount", "--name", "--network", "--net", "--oom-score-adj", "--pid",
    "--pids-limit", "--platform", "--publish", "--pull", "--restart", "--runtime", "--security-opt",
    "--shm-size", "--stop-signal", "--stop-timeout", "--tmpfs", "--ulimit", "--user", "--volume",
    "--volumes-from", "--workdir",
}
_RUN_VALUE_SHORT = set("aeplhmcuvwl")


def _run_split(args: list[str]) -> tuple[list[tuple[str, str]], int]:
    """Parse the arguments after `docker run`: ([(option, value)], index of the image).

    Option parsing stops at the image: everything after it belongs to the program in the container
    (`docker run img prog -d` is not a detached run). The index is len(args) when there is no image.
    """
    opts: list[tuple[str, str]] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--":
            return opts, i + 1
        if not a.startswith("-") or a == "-":
            return opts, i
        if a.startswith("--"):
            name, eq, val = a.partition("=")
            if not eq and name in _RUN_VALUE_OPTS and i + 1 < len(args):
                val = args[i + 1]
                i += 1
            opts.append((name.lower(), val))
        else:  # a cluster of short flags, such as -d, -it, -p8080:80, -v data:/d
            for j, ch in enumerate(a[1:], 1):
                if ch in _RUN_VALUE_SHORT:
                    val = a[j + 1:]
                    if not val and i + 1 < len(args):
                        val = args[i + 1]
                        i += 1
                    opts.append(("-" + ch, val))
                    break
                opts.append(("-" + ch, ""))
        i += 1
    return opts, i


def _run_detached(args: list[str]) -> bool:
    return any(o in {"-d", "--detach"} for o, _ in _run_split(args)[0])


def _compose_foreground(sub: str, after: list[str]) -> bool:
    if sub == "up":
        return not _detached(after)
    if sub == "run":
        return not _run_detached(after)  # options end at the service; a later -d is the program's
    return False


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
    for opt, val in _run_split(args)[0]:
        if opt == "--gpus":
            gpu = True
        elif opt == "--device" and "nvidia" in val.lower():
            gpu = True
        elif opt == "--runtime" and "nvidia" in val.lower():
            gpu = True
        elif opt in {"--name", "--label", "-l"}:
            named = True
    return gpu, named


# `docker start` options that take a value.
_START_VALUE_OPTS = {"--detach-keys"}


def _container_names(args: list[str]) -> list[str]:
    """The container names in the arguments after `docker start` or `docker restart`."""
    names, skip = [], False
    for a in args:
        if skip:
            skip = False
        elif a in _START_VALUE_OPTS or a in {"-t", "--time"}:
            skip = True
        elif not a.startswith("-"):
            names.append(a)
    return names


def _container_requests_gpu(names: list[str]) -> bool:
    """True when `docker inspect` says one of these existing containers asks for a GPU.

    Fails open (False) when docker is missing, slow or answers something unexpected.
    """
    if not names:
        return False
    try:
        out = subprocess.run(
            ["docker", "inspect", "--format", "{{json .HostConfig.DeviceRequests}} {{.HostConfig.Runtime}}", *names],
            capture_output=True, text=True, timeout=8, check=False,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    for line in out.splitlines():
        low = line.lower()
        if "nvidia" in low or '"gpu"' in low:
            return True
    return False


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


_UP_VALUE_OPTS = {"--attach", "--no-attach", "--exit-code-from", "--scale", "-t", "--timeout", "--wait-timeout",
                  "--pull"}


def _up_services(args: list[str]) -> list[str]:
    """Service names given to `compose up` (empty means all services)."""
    after = _compose_subcommand(args)[1]
    names, skip = [], False
    for a in after:
        if skip:
            skip = False
        elif a in _UP_VALUE_OPTS:
            skip = True
        elif not a.startswith("-"):
            names.append(a)
    return names


def _service_is_gpu(service: object) -> bool:
    """A compose service definition that asks for a GPU: `gpus:`, `runtime: nvidia` or a GPU device reservation."""
    if not isinstance(service, dict):
        return False
    if service.get("gpus") or str(service.get("runtime", "")).lower() == "nvidia":
        return True
    try:
        devices = service["deploy"]["resources"]["reservations"]["devices"]
    except (KeyError, TypeError):
        return False
    return isinstance(devices, list) and any(
        isinstance(d, dict) and (str(d.get("driver", "")).lower() == "nvidia" or "gpu" in map(str, d.get("capabilities") or []))
        for d in devices
    )


def _gpu_services_started(files: list[Path], named: list[str]) -> bool | None:
    """Whether `up <named>` starts a GPU service, counting `depends_on` and the files merged in order.

    None when the files cannot be parsed (no PyYAML, bad YAML): the caller then falls back to "the
    file mentions a GPU anywhere".
    """
    try:
        import yaml

        services: dict[str, dict] = {}
        for f in files:
            data = yaml.safe_load(f.read_text(encoding="utf-8", errors="replace")) or {}
            for name, body in (data.get("services") or {}).items():
                merged = services.setdefault(name, {"gpu": False, "deps": set()})
                if isinstance(body, dict):
                    merged["gpu"] = merged["gpu"] or _service_is_gpu(body)
                    deps = body.get("depends_on") or []
                    merged["deps"].update(deps.keys() if isinstance(deps, dict) else [d for d in deps if isinstance(d, str)])
    except Exception:  # noqa: BLE001
        return None
    pending, seen = list(named or services), set()
    while pending:
        name = pending.pop()
        if name in seen or name not in services:
            continue
        seen.add(name)
        svc = services[name]
        if svc["gpu"]:
            return True
        pending.extend(svc["deps"])
    return False


def _compose_up_gpu(args: list[str], cwd: Path) -> bool:
    if "up" not in args:
        return False
    files = [f for f in _compose_files(args, cwd) if f.is_file()]
    if not files:
        return False
    precise = _gpu_services_started(files, _up_services(args))
    if precise is not None:
        return precise
    for f in files:
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
        timed = any(_name(w) in _TIMEOUTS for w in words[: starts[0]])
        words = words[starts[0]:]
        head = _name(words[0])
        shown = " ".join(words)[:100]
        if timed:
            if head == "docker" and len(words) > 1:
                rest = words[2:] if words[1] == "container" else words[1:]
                if rest and rest[0] == "run" and not _run_detached(rest[1:]):
                    return _TIMEOUT.format(cmd=shown)
                if rest and rest[0] == "compose":
                    sub, after = _compose_subcommand(rest[1:])
                    if _compose_foreground(sub, after):
                        return _TIMEOUT.format(cmd=shown)
            elif head == "docker-compose":
                sub, after = _compose_subcommand(words[1:])
                if _compose_foreground(sub, after):
                    return _TIMEOUT.format(cmd=shown)
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
            elif rest[0] in {"start", "restart"} and not guarded and _container_requests_gpu(
                _container_names(rest[1:])
            ):
                return _UNGUARDED.format(cmd=shown)
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
