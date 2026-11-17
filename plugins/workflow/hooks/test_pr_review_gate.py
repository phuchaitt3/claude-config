import io
import json

import pytest

import pr_review_gate as gate


@pytest.mark.parametrize(
    "command,expected",
    [
        ("gh pr create --title x", True),
        ("gh pr comment 4 --body y", True),
        ("gh pr merge 4 --squash", True),
        ("gh -R o/r pr merge 4", True),
        ("gh pr view 4", False),
        ("gh pr checks 4 --watch", False),
        ("ls", False),
    ],
)
def test_which_commands_need_the_skill(command, expected):
    assert gate.needs_skill(command) is expected


def test_skill_call_and_slash_command_both_count(tmp_path):
    call = tmp_path / "a.jsonl"
    call.write_text('{"name":"Skill","input":{"skill":"workflow:pr-review"}}\n', encoding="utf-8")
    slash = tmp_path / "b.jsonl"
    slash.write_text("<command-name>/workflow:pr-review</command-name>\n", encoding="utf-8")
    other = tmp_path / "c.jsonl"
    other.write_text('{"name":"Skill","input":{"skill":"workflow:git"}}\n', encoding="utf-8")
    assert gate.skill_loaded(call) and gate.skill_loaded(slash) and not gate.skill_loaded(other)


def _run(monkeypatch, capsys, payload):
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert gate.main() == 0
    return capsys.readouterr().out


def test_denies_without_the_skill_and_allows_after(tmp_path, monkeypatch, capsys):
    t = tmp_path / "t.jsonl"
    t.write_text("{}\n", encoding="utf-8")
    payload = {"tool_name": "Bash", "tool_input": {"command": "gh pr create"},
               "transcript_path": str(t)}
    out = json.loads(_run(monkeypatch, capsys, payload))
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "workflow:pr-review" in out["hookSpecificOutput"]["permissionDecisionReason"]
    t.write_text('{"input":{"skill":"workflow:pr-review"}}\n', encoding="utf-8")
    assert _run(monkeypatch, capsys, payload) == ""


def test_fails_open(tmp_path, monkeypatch, capsys):
    gone = {"tool_name": "Bash", "tool_input": {"command": "gh pr comment 1"},
            "transcript_path": str(tmp_path / "missing.jsonl")}
    assert _run(monkeypatch, capsys, gone) == ""
    none = {"tool_name": "Bash", "tool_input": {"command": "gh pr comment 1"}}
    assert _run(monkeypatch, capsys, none) == ""
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    assert gate.main() == 0
