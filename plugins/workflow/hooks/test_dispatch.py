import importlib.util
import json
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("dispatch", Path(__file__).with_name("dispatch.py"))
assert _spec and _spec.loader
dispatch = importlib.util.module_from_spec(_spec)
sys.modules["dispatch"] = dispatch
_spec.loader.exec_module(dispatch)


def check(tmp_path, name, body):
    d = tmp_path / "checks"
    d.mkdir(exist_ok=True)
    (d / name).write_text(body, encoding="utf-8")
    return d


def pre(tool="Bash"):
    return {"hook_event_name": "PreToolUse", "tool_name": tool}


def test_joins_texts_of_matching_checks_in_name_order(tmp_path):
    check(tmp_path, "b.py", "def run(p):\n    return 'B'\n")
    d = check(tmp_path, "a.py", "def run(p):\n    return 'A'\n")
    assert dispatch.run_checks(pre(), d) == ["A", "B"]


def test_filters_by_event_and_tool(tmp_path):
    d = check(tmp_path, "w.py", "EVENTS={'PreToolUse'}\nTOOLS={'ScheduleWakeup'}\n"
                                "def run(p):\n    return 'W'\n")
    assert dispatch.run_checks(pre("ScheduleWakeup"), d) == ["W"]
    assert dispatch.run_checks(pre("Bash"), d) == []
    assert dispatch.run_checks({"hook_event_name": "Stop"}, d) == []


def test_a_raising_check_is_skipped_and_logged(tmp_path, monkeypatch):
    monkeypatch.setattr(dispatch, "ERROR_LOG", tmp_path / "err.log")
    check(tmp_path, "a.py", "def run(p):\n    raise RuntimeError('boom')\n")
    d = check(tmp_path, "b.py", "def run(p):\n    return 'B'\n")
    assert dispatch.run_checks(pre(), d) == ["B"]
    assert "a.py" in (tmp_path / "err.log").read_text()


def test_a_syntax_error_in_one_check_does_not_hide_others(tmp_path, monkeypatch):
    monkeypatch.setattr(dispatch, "ERROR_LOG", tmp_path / "err.log")
    check(tmp_path, "a.py", "def run(p) return\n")
    d = check(tmp_path, "b.py", "def run(p):\n    return 'B'\n")
    assert dispatch.run_checks(pre(), d) == ["B"]


def test_underscore_and_test_files_are_not_loaded(tmp_path):
    check(tmp_path, "_helper.py", "def run(p):\n    return 'H'\n")
    d = check(tmp_path, "test_x.py", "def run(p):\n    return 'T'\n")
    assert dispatch.run_checks(pre(), d) == []


def test_unknown_event_and_missing_dir_are_silent(tmp_path):
    assert dispatch.run_checks({"hook_event_name": "SessionStart"}, tmp_path) == []
    assert dispatch.run_checks(pre(), tmp_path / "none") == []


def test_none_or_empty_result_adds_nothing(tmp_path):
    check(tmp_path, "a.py", "def run(p):\n    return None\n")
    d = check(tmp_path, "b.py", "def run(p):\n    return ''\n")
    assert dispatch.run_checks(pre(), d) == []


def test_context_check_fires_through_the_real_checks_dir(tmp_path):
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"type": "assistant", "message": {"usage": {
        "input_tokens": 0, "cache_read_input_tokens": 250000,
        "cache_creation_input_tokens": 0}}}) + "\n", encoding="utf-8")
    payload = {"hook_event_name": "PreToolUse", "tool_name": "ScheduleWakeup",
               "tool_input": {"delaySeconds": 60}, "transcript_path": str(t)}
    texts = dispatch.run_checks(payload)
    assert len(texts) == 1 and "250000" in texts[0]
    payload["tool_name"] = "Bash"
    assert dispatch.run_checks(payload) == []
