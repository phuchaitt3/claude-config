"""UserPromptSubmit hook: notice GPU use that bypasses the machine-wide lock.

`~/claude-config/scripts/gpu_run.py` holds a lock around every GPU job and logs who used the GPU.
A job that ignores it (a notebook, a script run by hand) cannot be seen in that log. This hook asks
`nvidia-smi` at most once every two minutes: when the GPU is busy and nobody holds the lock, it
logs an `unguarded` event (at most one per ten minutes) and tells the chat in one line, so the user
finds out from `gpu_run.py report` and the chat can say so. Silent otherwise, and silent on a
machine without an NVIDIA GPU or without the script (a broken hook must never block a session).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

SCRIPTS = Path.home() / "claude-config" / "scripts"
CACHE = Path.home() / ".claude" / "hook-cache" / "gpu_watch.json"
CHECK_EVERY_S = 120
LOG_EVERY_S = 600


def decide(
    state: dict, now: float, reading: dict | None, locked: bool, busy: bool, ollama: list[dict] | None = None
) -> tuple[dict, str, bool]:
    """(new state, text for the chat, whether to log an event). `ollama` lists the models Ollama has
    loaded; when they account for the GPU memory, the text names them instead of "unguarded"."""
    state = dict(state, checked=now)
    if reading is None or locked or not busy:
        return state, "", False
    log = now - state.get("logged", 0) >= LOG_EVERY_S
    if log:
        state["logged"] = now
    if not log:
        return state, "", False
    ollama_mb = sum(m["vram_mb"] for m in ollama or [])
    if ollama_mb and reading["mem_mb"] - ollama_mb < 300:
        names = ", ".join(m["name"] for m in ollama or [])
        text = (
            f"GPU memory ({reading['mem_mb']:.0f} MB) is Ollama's loaded models ({names}), outside the "
            "machine-wide lock. Before a GPU job, run it with `gpu_run.py run --stop-ollama` (or `hold`) "
            "if no other chat is using Ollama now."
        )
    else:
        text = (
            f"GPU is {reading['util_pct']:.0f}% busy ({reading['mem_mb']:.0f} MB) but no job holds the "
            "machine-wide lock: something is using the laptop GPU outside `gpu_run.py` (a GPU container "
            "started without `gpu_run.py hold`?). Do not start a GPU job until it ends or you know what "
            "it is; the user sees it in `gpu_run.py report`."
        )
    return state, text, log


def main() -> None:
    sys.path.insert(0, str(SCRIPTS))
    import gpu_run

    try:
        state = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    now = time.time()
    if now - state.get("checked", 0) < CHECK_EVERY_S:
        return
    reading = gpu_run.gpu_reading()
    locked = bool(reading) and gpu_run.Lock().is_held()
    busy = bool(reading) and (
        reading["util_pct"] >= gpu_run.IDLE_UTIL_PCT or reading["mem_mb"] >= gpu_run.IDLE_MEM_MB
    )
    ollama = gpu_run.ollama_models() if busy and not locked else []
    state, text, log = decide(state, now, reading, locked, busy, ollama)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(state), encoding="utf-8")
    if log and reading:
        kind = gpu_run.classify(reading, locked, sum(m["vram_mb"] for m in ollama))
        gpu_run.log_event("ollama" if kind == "ollama" else "unguarded", source="hook", **reading)
    if text:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": text}}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
