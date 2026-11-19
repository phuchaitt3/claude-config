import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).with_name("worktree_tool_guard.py")


def run(tool, env_extra=None, transcript=None):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_LOOP_KEEPALIVE"}
    env.update(env_extra or {})
    payload = {"tool_name": tool, "tool_input": {"name": "x"}}
    if transcript:
        payload["transcript_path"] = str(transcript)
    out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                         capture_output=True, text=True, env=env, timeout=30)
    assert out.returncode == 0
    return json.loads(out.stdout) if out.stdout.strip() else None


def test_denies_enter_and_exit_when_keepalive_set():
    for tool in ("EnterWorktree", "ExitWorktree"):
        r = run(tool, {"CLAUDE_CODE_LOOP_KEEPALIVE": "1"})
        h = r["hookSpecificOutput"]
        assert h["hookEventName"] == "PreToolUse" and h["permissionDecision"] == "deny"
        assert "git worktree add" in h["permissionDecisionReason"]


def test_silent_in_ordinary_chat():
    assert run("EnterWorktree") is None


def test_silent_for_other_tools():
    assert run("Edit", {"CLAUDE_CODE_LOOP_KEEPALIVE": "1"}) is None


def test_denies_when_transcript_shows_live_loop(tmp_path):
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "ScheduleWakeup", "input": {"delaySeconds": 1200}}]}}) + "\n")
    assert run("EnterWorktree", transcript=t)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_silent_on_bad_input():
    out = subprocess.run([sys.executable, str(HOOK)], input="not json",
                         capture_output=True, text=True, timeout=30)
    assert out.returncode == 0 and out.stdout == ""
