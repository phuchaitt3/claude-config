import io
import json

import pytest

import kaggle_guard


@pytest.mark.parametrize("command", [
    "kaggle kernels push",
    "kaggle kernels push -p build/kaggle",
    "kaggle k push -p x",
    "kaggle kernels update -p x",
    "cd build; kaggle.exe kernels push -p .",
    "PYTHONUTF8=1 uv run kaggle kernels push -p x",
    "uvx kaggle kernels push -p x",
    "python -m kaggle kernels push -p x",
])
def test_refuses_raw_pushes(command):
    assert kaggle_guard.refusal(command)


@pytest.mark.parametrize("command", [
    "kaggle kernels status me/a/2",
    "kaggle kernels push --help",
    "kaggle kernels push -p x --no-run",
    "python ~/claude-config/scripts/kaggle_slots.py push -p x",
    "python tools/kaggle_run.py push",
    "git commit -m 'guard kaggle kernels push'",
    "echo kaggle kernels push",
])
def test_passes_everything_else(command):
    assert not kaggle_guard.refusal(command)


def test_hook_denies(monkeypatch, capsys):
    payload = {"tool_name": "Bash", "tool_input": {"command": "kaggle kernels push -p x"}}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert kaggle_guard.main() == 0
    out = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert out["permissionDecision"] == "deny"
