import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("standard_nudge.py")


def run(payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)], input=payload, capture_output=True, text=True, encoding="utf-8", check=False
    )


def test_web_search_gets_the_reminder() -> None:
    result = run(json.dumps({"tool_name": "WebSearch", "tool_input": {"query": "x"}}))
    assert result.returncode == 0
    out = json.loads(result.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PostToolUse"
    assert "standard:" in out["additionalContext"]


def test_web_fetch_gets_the_reminder() -> None:
    result = run(json.dumps({"tool_name": "WebFetch", "tool_input": {"url": "https://example.com"}}))
    assert "standard:" in result.stdout


def test_other_tools_get_nothing() -> None:
    result = run(json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}))
    assert result.returncode == 0
    assert result.stdout == ""


def test_bad_input_fails_open() -> None:
    result = run("not json")
    assert result.returncode == 0
    assert result.stdout == ""
