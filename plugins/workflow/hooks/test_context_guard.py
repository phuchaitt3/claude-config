import importlib.util
import json
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "context_guard", Path(__file__).with_name("context_guard.py")
)
assert _spec and _spec.loader
context_guard = importlib.util.module_from_spec(_spec)
sys.modules["context_guard"] = context_guard
_spec.loader.exec_module(context_guard)


def call(read=0, write=0, inp=0, side=False):
    return json.dumps({"type": "assistant", "isSidechain": side, "message": {"usage": {
        "input_tokens": inp, "cache_read_input_tokens": read,
        "cache_creation_input_tokens": write}}})


def transcript(tmp_path, *lines):
    p = tmp_path / "t.jsonl"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


def payload(path, tool="ScheduleWakeup", **inp):
    return {"tool_name": tool, "tool_input": inp or {"delaySeconds": 60, "prompt": "p"},
            "transcript_path": path}


def test_over_threshold_reminds_with_size(tmp_path):
    p = transcript(tmp_path, call(read=150000, write=40000, inp=30000))
    text = context_guard.reminder(payload(p))
    assert text and "220000" in text


def test_at_or_under_threshold_is_silent(tmp_path):
    p = transcript(tmp_path, call(read=199000, write=1000))
    assert context_guard.reminder(payload(p)) is None


def test_uses_the_last_call_not_the_peak(tmp_path):
    p = transcript(tmp_path, call(read=250000), call(read=90000))
    assert context_guard.reminder(payload(p)) is None


def test_stop_call_is_silent(tmp_path):
    p = transcript(tmp_path, call(read=250000))
    assert context_guard.reminder(payload(p, stop=True)) is None


def test_other_tool_is_silent(tmp_path):
    p = transcript(tmp_path, call(read=250000))
    assert context_guard.reminder(payload(p, tool="Bash")) is None


def test_sidechain_calls_are_ignored(tmp_path):
    p = transcript(tmp_path, call(read=90000), call(read=300000, side=True))
    assert context_guard.reminder(payload(p)) is None


def test_missing_transcript_or_usage_is_silent(tmp_path):
    assert context_guard.reminder(payload(str(tmp_path / "none.jsonl"))) is None
    assert context_guard.reminder(payload(transcript(tmp_path, "{}"))) is None
    assert context_guard.reminder({"tool_name": "ScheduleWakeup"}) is None


def test_garbage_lines_are_skipped(tmp_path):
    p = transcript(tmp_path, call(read=220000), "not json", '{"usage": ')
    assert "220000" in context_guard.reminder(payload(p))


def test_threshold_matches_context_size():
    src = Path(__file__).parents[1] / "skills" / "self-drive" / "context_size.py"
    spec = importlib.util.spec_from_file_location("context_size", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert context_guard.THRESHOLD == mod.DEFAULT_THRESHOLD
