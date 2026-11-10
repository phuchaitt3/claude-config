"""Tests for keep_awake.py: which background commands hold, and how the tool's shell is recognised."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("keep_awake", Path(__file__).with_name("keep_awake.py"))
ka = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ka)


@pytest.mark.parametrize("command", [
    "uv run python scripts/benchmark.py --chunks 500000",
    "pytest -x tests/",
    "docker compose up -d qdrant",
    "docker compose up --detach",
    "docker-compose up -d",
    "python reserve.py",          # "serve" inside a word is not a server
    "npm run build",
    "ls",
])
def test_jobs_hold(command):
    assert ka.wants_hold(command)


@pytest.mark.parametrize("command", [
    "pnpm dev",
    "pnpm run dev --port 3001",
    "npm run dev",
    "cd apps/web && next dev",
    "uv run uvicorn app.main:app --reload",
    "pytest --watch",
    "npx serve out",
    "ollama serve",
    "docker compose up",
    "docker compose up qdrant",
    "docker compose -f compose.yaml up api",
])
def test_servers_skip(command):
    assert not ka.wants_hold(command)


def test_marker_overrides_both_ways():
    assert ka.wants_hold("pnpm dev  # keepawake: on")
    assert not ka.wants_hold("uv run python long_job.py # keepawake: off")
    assert ka.wants_hold("python x.py # KeepAwake: ON")
    assert not ka.wants_hold("python x.py # keepawake: on\n# keepawake: off")  # last one wins


def test_compose_up_detach_in_one_segment_only():
    # The second `up` has no -d, so it is a foreground server.
    assert not ka.wants_hold("docker compose up -d db; docker compose up api")


def test_fingerprint_takes_long_distinct_words():
    words = ka.fingerprint("uv run python scripts/benchmark.py --chunks 500000")
    assert words[0] == "benchmark"
    assert all(len(w) >= 4 for w in words) and len(words) <= 4
    assert ka.fingerprint("ls -la") == []


BASH_LINE = (
    '"C:\\Program Files\\Git\\bin\\bash.exe" -c "source /c/Users/x/.claude/shell-snapshots/s.sh '
    "&& eval 'uv run python scripts/benchmark.py --chunks 500000'\""
)
PS_LINE = (
    'C:\\WINDOWS\\System32\\cmd.exe /d /s /c ""pwsh.exe" -Command "$s = $env:'
    'CLAUDE_CODE_SHELL_LAUNCHER_SCRIPT; Invoke-Expression $s""'
)
HOOK_LINE = '"C:\\Program Files\\Git\\bin\\bash.exe" -c "python /c/x/hooks/push_guard.py"'


def test_bash_shell_matched_by_words():
    words = ka.fingerprint("uv run python scripts/benchmark.py --chunks 500000")
    assert ka.matches_shell("Bash", "bash.exe", BASH_LINE, words)
    assert not ka.matches_shell("Bash", "bash.exe", HOOK_LINE, words)
    assert not ka.matches_shell("Bash", "cmd.exe", BASH_LINE, words)


def test_bash_without_words_needs_the_tool_preamble():
    assert ka.matches_shell("Bash", "bash.exe", BASH_LINE, [])
    assert not ka.matches_shell("Bash", "bash.exe", HOOK_LINE, [])


def test_powershell_shell_matched_by_launcher():
    assert ka.matches_shell("PowerShell", "cmd.exe", PS_LINE, ["anything"])
    assert not ka.matches_shell("PowerShell", "cmd.exe", "cmd /c python hook.py", [])
    assert not ka.matches_shell("Bash", "bash.exe", PS_LINE, [])


def test_status_line_names_count_and_oldest():
    now = 100_000.0
    holds = [
        {"holder": 1, "started": now - 9 * 3600, "command": "uv run python long.py"},
        {"holder": 2, "started": now - 60, "command": "pytest"},
    ]
    line = ka.status_line(holds, now)
    assert line.startswith("keep-awake: 2 holds (oldest 9 h: uv run python long.py)")
    assert ka.status_line([], now) == ""
    assert "1 hold (oldest 5 min" in ka.status_line(holds[1:], now + 240)


def test_status_line_truncates_long_commands():
    line = ka.status_line([{"holder": 1, "started": 0.0, "command": "x " * 100}], 10.0)
    assert "..." in line and len(line) < 220


def test_claude_pid_walks_up_to_claude():
    procs = {10: (9, "python.exe"), 9: (8, "bash.exe"), 8: (7, "claude.exe"), 7: (1, "Code.exe")}
    assert ka.claude_pid(procs, 10) == 8
    assert ka.claude_pid({10: (9, "python.exe")}, 10) is None
    assert ka.claude_pid({10: (10, "python.exe")}, 10) is None  # a loop ends


def _run_hook(monkeypatch, payload, started):
    monkeypatch.setattr(ka, "start_holder", lambda p: started.append(p))
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(sys, "platform", "win32")
    assert ka.main([]) == 0


def test_hook_starts_holder_only_for_background_jobs(monkeypatch):
    started: list = []
    _run_hook(monkeypatch, {"tool_name": "Bash", "tool_input": {"command": "pytest"}}, started)
    assert started == []  # foreground
    job = {"tool_name": "Bash", "tool_input": {"command": "pytest", "run_in_background": True}}
    _run_hook(monkeypatch, job, started)
    assert len(started) == 1
    server = {"tool_name": "PowerShell", "tool_input": {"command": "pnpm dev", "run_in_background": True}}
    _run_hook(monkeypatch, server, started)
    assert len(started) == 1
    other = {"tool_name": "Monitor", "tool_input": {"command": "pytest", "run_in_background": True}}
    _run_hook(monkeypatch, other, started)
    assert len(started) == 1


def test_hook_fails_open(monkeypatch, capsys):
    def boom(_payload):
        raise RuntimeError("no toolhelp")

    monkeypatch.setattr(ka, "start_holder", boom)
    monkeypatch.setattr(ka, "log", lambda _m: None)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": "pytest", "run_in_background": True}})))
    monkeypatch.setattr(sys, "platform", "win32")
    assert ka.main([]) == 0
    assert capsys.readouterr().out == ""


def test_status_reports_changes_only(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(ka, "CACHE_DIR", tmp_path)
    holds = [{"holder": 5, "started": 0.0, "command": "pytest"}]
    monkeypatch.setattr(ka, "active_holds", lambda: holds)
    monkeypatch.setattr(ka.time, "time", lambda: 600.0)
    ka.status({"session_id": "s1"})
    assert "keep-awake: 1 hold" in capsys.readouterr().out
    ka.status({"session_id": "s1"})
    assert capsys.readouterr().out == ""  # unchanged
    holds.clear()
    ka.status({"session_id": "s1"})
    assert "no holds" in capsys.readouterr().out  # the end is reported once
    ka.status({"session_id": "s1"})
    assert capsys.readouterr().out == ""


def test_status_repeats_while_a_hold_is_long(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(ka, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(ka, "active_holds", lambda: [{"holder": 5, "started": 0.0, "command": "x"}])
    monkeypatch.setattr(ka.time, "time", lambda: 5 * 3600.0)
    ka.status({"session_id": "s2"})
    ka.status({"session_id": "s2"})
    assert capsys.readouterr().out.count("keep-awake: 1 hold") == 2


def test_two_holders_never_claim_the_same_shell(tmp_path):
    live = {101, 102}
    assert ka.claim_shell(500, 101, tmp_path, live.__contains__)
    assert not ka.claim_shell(500, 102, tmp_path, live.__contains__)  # taken by a live holder
    assert ka.claim_shell(501, 102, tmp_path, live.__contains__)      # so it takes the next shell


def test_claim_left_by_a_dead_holder_is_taken_over(tmp_path):
    (tmp_path / "500.claim").write_text("999", encoding="utf-8")
    assert ka.claim_shell(500, 101, tmp_path, lambda pid: pid == 101)
    assert (tmp_path / "500.claim").read_text(encoding="utf-8") == "101"
