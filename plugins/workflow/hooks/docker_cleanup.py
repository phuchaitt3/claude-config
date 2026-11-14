"""Docker cleanup (claude-config, user's decision 2026-11-14, after eight stopped containers from
finished tasks were found on a laptop; no rule or hook had asked a chat to remove them).

A chat that starts a container for a task removes it when the task ends. A text rule left eight
behind, so this hook enforces it. Three modes, each failing open (a broken hook never traps a turn):

- PreToolUse (Bash|PowerShell), no argument: when the command can create a container
  (`docker run`, `docker create`, `docker compose up|run`), saves the ids of all containers that
  exist now.
- `post` (PostToolUse): diffs against that snapshot and adds the new containers to this session's
  list. Attribution is per command, so another chat's containers are never listed.
- `stop` (Stop): when any container this session started still exists, blocks the end of the turn
  once (`stop_hook_active`) with the commands to remove them. A container kept on purpose (a
  `gpu_run.py hold` service, a dev database the user is using) is named in the final message instead.

It never removes anything and never touches volumes: `down` without `-v` keeps them. State is local
(`~/.claude/hook-cache/docker_cleanup/<session>.json`).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

CACHE = Path.home() / ".claude" / "hook-cache" / "docker_cleanup"
_START = re.compile(
    r"\bdocker\s+(?:container\s+)?(?:run|create)\b"
    r"|\bdocker(?:-compose|\s+compose)\b(?:\s+-\S+(?:\s+[^-\s]\S*)?)*\s+(?:up|run)\b"
)


def can_create(command: str) -> bool:
    """True when the command can start or create a container."""
    return bool(_START.search(command))


def _docker(args: list[str]) -> str | None:
    try:
        done = subprocess.run(
            ["docker", *args], capture_output=True, text=True, timeout=8, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def all_ids() -> set[str] | None:
    out = _docker(["ps", "-a", "-q", "--no-trunc"])
    return None if out is None else {line.strip() for line in out.splitlines() if line.strip()}


def _state_path(session: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session)[:80] or "unknown"
    return CACHE / f"{safe}.json"


def load(session: str) -> dict:
    try:
        data = json.loads(_state_path(session).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data.setdefault("pre", {})
    data.setdefault("owned", [])
    return data


def save(session: str, data: dict) -> None:
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        _state_path(session).write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass


def pre(payload: dict) -> None:
    command = str((payload.get("tool_input") or {}).get("command", ""))
    session = str(payload.get("session_id", ""))
    if not session or not can_create(command):
        return
    ids = all_ids()
    if ids is None:
        return
    data = load(session)
    data["pre"][str(payload.get("tool_use_id", "last"))] = sorted(ids)
    save(session, data)


def post(payload: dict) -> None:
    session = str(payload.get("session_id", ""))
    key = str(payload.get("tool_use_id", "last"))
    data = load(session) if session else {}
    before = data.get("pre", {}).pop(key, None) if data else None
    if before is None:
        return
    now = all_ids()
    if now is None:
        return
    owned = set(data["owned"])
    data["owned"] = sorted(owned | (now - set(before)))
    save(session, data)


def survivors(owned: list[str]) -> list[dict]:
    """Containers from the list that still exist: name, status, compose project."""
    if not owned:
        return []
    fmt = '{{.ID}}|{{.Names}}|{{.Status}}|{{.Label "com.docker.compose.project"}}'
    args = ["ps", "-a", "--no-trunc", "--format", fmt]
    for cid in owned:
        args += ["--filter", f"id={cid}"]
    out = _docker(args)
    rows = []
    for line in (out or "").splitlines():
        cid, name, status, project = (line.split("|") + ["", "", "", ""])[:4]
        if cid in owned:
            rows.append({"id": cid, "name": name, "status": status, "project": project})
    return rows


def message(rows: list[dict]) -> str:
    projects = sorted({r["project"] for r in rows if r["project"]})
    loose = [r["name"] for r in rows if not r["project"]]
    lines = [
        "Docker cleanup: this chat started containers that still exist ("
        + ", ".join(f"{r['name']} [{r['status']}]" for r in rows)
        + "). Remove them when the task is done:"
    ]
    lines += [f"  docker compose -p {p} down   (no -v: volumes stay)" for p in projects]
    if loose:
        lines.append("  docker rm -f " + " ".join(loose))
    lines.append(
        "A container kept on purpose (a held GPU service, a database the user is using): "
        "say so and why in your final message instead. Never delete volumes without the user's yes."
    )
    return "\n".join(lines)


def stop(payload: dict) -> dict | None:
    if payload.get("stop_hook_active"):
        return None
    session = str(payload.get("session_id", ""))
    owned = load(session)["owned"] if session else []
    rows = survivors(owned)
    if not rows:
        return None
    return {"decision": "block", "reason": message(rows)}


def main(argv: list[str]) -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return 0
        mode = argv[1] if len(argv) > 1 else "pre"
        if mode == "post":
            post(payload)
        elif mode == "stop":
            result = stop(payload)
            if result:
                json.dump(result, sys.stdout)
        else:
            pre(payload)
    except Exception:  # fail open
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
