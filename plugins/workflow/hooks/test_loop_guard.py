import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "loop_guard", Path(__file__).with_name("loop_guard.py")
)
assert _spec and _spec.loader
loop_guard = importlib.util.module_from_spec(_spec)
sys.modules["loop_guard"] = loop_guard
_spec.loader.exec_module(loop_guard)


def start():
    return {"type": "user", "message": {"content": "# /loop - schedule\n> Each round:\n1. Sync"}}


def wake(stop=False):
    inp = {"stop": True} if stop else {"delaySeconds": 60, "prompt": "p"}
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "ScheduleWakeup", "input": inp}]}}


def chat():
    return {"type": "user", "message": {"content": "hello"}}


def payload(crons=(), tasks=(), active=False):
    return {"stop_hook_active": active, "session_crons": list(crons),
            "background_tasks": list(tasks)}


def test_loop_started_and_never_rescheduled_nudges():
    assert loop_guard.should_nudge(payload(), [start()])


def test_pending_wakeup_is_silent():
    assert not loop_guard.should_nudge(payload(crons=[{"id": "c"}]), [start(), wake()])


def test_deliberate_stop_is_silent():
    assert not loop_guard.should_nudge(payload(), [start(), wake(), wake(stop=True)])


def test_new_loop_after_stop_is_live_again():
    assert loop_guard.should_nudge(payload(), [start(), wake(stop=True), start()])


def test_running_background_task_is_silent():
    tasks = [{"id": "t", "status": "running", "type": "subagent"}]
    assert not loop_guard.should_nudge(payload(tasks=tasks), [start()])


def test_finished_background_task_does_not_block_the_nudge():
    tasks = [{"id": "t", "status": "completed", "type": "subagent"}]
    assert loop_guard.should_nudge(payload(tasks=tasks), [start()])


def test_ordinary_chat_is_silent():
    assert not loop_guard.should_nudge(payload(), [chat()])


def test_slash_loop_mentioned_mid_message_is_silent():
    other = {"type": "user", "message": {"content": "please explain what # /loop does"}}
    assert not loop_guard.should_nudge(payload(), [other])


def test_loop_start_as_a_text_block_list_counts():
    entry = {"type": "user", "message": {"content": [{"type": "text", "text": "# /loop x"}]}}
    assert loop_guard.should_nudge(payload(), [entry])


def test_stop_hook_active_is_silent():
    assert not loop_guard.should_nudge(payload(active=True), [start()])


@pytest.mark.parametrize("bad", [{}, {"session_crons": []}, {"background_tasks": []}])
def test_missing_registry_fields_are_silent(bad):
    assert not loop_guard.should_nudge(bad, [start()])


def run_main(monkeypatch, tmp_path, entries, pl):
    path = tmp_path / "t.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\nnot json\n", encoding="utf-8")
    pl = dict(pl, transcript_path=str(path))
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(pl)))
    out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", out)
    assert loop_guard.main() == 0
    return out.getvalue()


def test_main_emits_additional_context(monkeypatch, tmp_path):
    out = json.loads(run_main(monkeypatch, tmp_path, [start()], payload()))
    assert out["hookSpecificOutput"]["hookEventName"] == "Stop"
    assert "ScheduleWakeup" in out["hookSpecificOutput"]["additionalContext"]


def test_main_silent_when_wakeup_pending(monkeypatch, tmp_path):
    assert run_main(monkeypatch, tmp_path, [start(), wake()], payload(crons=[{"id": "c"}])) == ""


def test_main_survives_garbage_stdin(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("not json"))
    assert loop_guard.main() == 0


def test_main_survives_missing_transcript(monkeypatch):
    pl = dict(payload(), transcript_path="Z:/nope/missing.jsonl")
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(pl)))
    assert loop_guard.main() == 0


def test_resume_with_live_loop_rearms():
    assert loop_guard.should_rearm({"source": "resume"}, [start(), wake()])


def test_resume_after_deliberate_stop_is_silent():
    assert not loop_guard.should_rearm({"source": "resume"}, [start(), wake(stop=True)])


def test_compact_keeps_wakeups_so_is_silent():
    assert not loop_guard.should_rearm({"source": "compact"}, [start(), wake()])


def test_ordinary_chat_resume_is_silent():
    assert not loop_guard.should_rearm({"source": "resume"}, [chat()])


def test_session_start_main_emits_rearm(tmp_path, monkeypatch, capsys):
    tr = tmp_path / "t.jsonl"
    tr.write_text("\n".join(json.dumps(e) for e in [start(), wake()]), encoding="utf-8")
    payload_ = {"hook_event_name": "SessionStart", "source": "resume", "transcript_path": str(tr)}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload_)))
    assert loop_guard.main() == 0
    out = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert out["hookEventName"] == "SessionStart"
    assert "Re-arm now" in out["additionalContext"]
