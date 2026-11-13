import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "loop_route_guard", Path(__file__).with_name("loop_route_guard.py"))
m = importlib.util.module_from_spec(_spec)
sys.modules["loop_route_guard"] = m
_spec.loader.exec_module(m)


def tool(name, **inp):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": name, "input": inp}]}}


START = {"type": "user", "message": {"content": "# /loop - schedule\n> Each round"}}


def edits(n):
    return [tool("Edit", file_path="a")] * n


def test_silent_without_loop():
    assert m.should_nudge(edits(20)) == 0


def test_silent_below_threshold():
    assert m.should_nudge([START] + edits(4)) == 0


def test_nudges_at_threshold_then_every_three():
    assert m.should_nudge([START] + edits(5)) == 5
    assert m.should_nudge([START] + edits(6)) == 0
    assert m.should_nudge([START] + edits(8)) == 8


def test_blocks_after_nine_edits():
    assert m.should_block([START] + edits(8), "src/a.py") == 0
    assert m.should_block([START] + edits(9), "src/a.py") == 9


def test_block_exempts_handoff_notes_and_lifts_on_delegation():
    assert m.should_block([START] + edits(12), "D:/x/.handoff/overnight-2026-11-14c.md") == 0
    assert m.should_block([START] + edits(12) + [tool("Agent")], "src/a.py") == 0


def test_block_silent_without_loop():
    assert m.should_block(edits(30), "src/a.py") == 0


def test_agent_call_resets():
    assert m.should_nudge([START] + edits(10) + [tool("Agent")] + edits(3)) == 0


def test_background_session_resets():
    e = [START] + edits(10) + [tool("Bash", command="claude --bg -n x 'brief'")] + edits(2)
    assert m.should_nudge(e) == 0


def test_stopped_loop_silent():
    stop = tool("ScheduleWakeup", stop=True)
    assert m.should_nudge([START] + edits(9) + [stop]) == 0
