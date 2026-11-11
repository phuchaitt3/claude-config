import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import run_estimate as re_


@pytest.mark.parametrize("command,expected", [
    ("python run.py  # estimate: 20m", 20.0),
    ("python run.py # estimate: 2h", 120.0),
    ("python run.py # estimate: 90s", 1.5),
    ("python run.py # estimate: 15", 15.0),
    ("python run.py # Estimate: 7.5 min", 7.5),
    ("python run.py # estimate: 5m # estimate: 9m", 9.0),
    ("python run.py", None),
    ("echo estimate: 5m", None),
])
def test_parse_estimate(command, expected):
    assert re_.parse_estimate(command) == expected


def entry(est, act):
    return {"estimate_min": est, "actual_min": act}


def test_ratio_needs_enough_tagged_runs():
    assert re_.ratio([entry(10, 12), entry(None, 5), entry(10, 11)]) is None
    r, n = re_.ratio([entry(10, 12), entry(20, 20), entry(30, 45), entry(None, 99)])
    assert (r, n) == (1.2, 3)


def test_ratio_uses_only_recent_runs():
    old = [entry(10, 100)] * 30
    recent = [entry(10, 10)] * re_.RECENT
    assert re_.ratio(old + recent) == (1.0, re_.RECENT)


def test_advice():
    assert re_.advice(20, [entry(10, 12)]) == ""
    line = re_.advice(20, [entry(10, 12), entry(10, 12), entry(10, 12)])
    assert "1.20x" in line and "about 24 min" in line


def test_record_and_read(tmp_path):
    log = tmp_path / "log.jsonl"
    re_.record("Bash", True, "python x.py   # estimate: 20m", 1020, path=log)
    re_.record("Bash", False, "ls", 5, path=log)
    rows = re_.read_log(log)
    assert rows[0]["estimate_min"] == 20.0 and rows[0]["actual_min"] == 17.0
    assert rows[0]["background"] is True and rows[1]["estimate_min"] is None
    assert re_.read_log(tmp_path / "missing.jsonl") == []


def test_foreground_pre_post(tmp_path, monkeypatch):
    monkeypatch.setattr(re_, "PENDING_DIR", tmp_path / "pending")
    monkeypatch.setattr(re_, "LOG", tmp_path / "log.jsonl")
    payload = {"tool_name": "Bash", "tool_use_id": "t1",
               "tool_input": {"command": "sleep 1 # estimate: 1m"}}
    re_.pre(payload)
    re_.post(payload)
    rows = re_.read_log(tmp_path / "log.jsonl")
    assert len(rows) == 1 and rows[0]["estimate_min"] == 1.0 and not rows[0]["background"]


def test_untagged_short_foreground_not_logged(tmp_path, monkeypatch):
    monkeypatch.setattr(re_, "PENDING_DIR", tmp_path / "pending")
    monkeypatch.setattr(re_, "LOG", tmp_path / "log.jsonl")
    payload = {"tool_name": "Bash", "tool_use_id": "t2", "tool_input": {"command": "ls"}}
    re_.pre(payload)
    re_.post(payload)
    assert re_.read_log(tmp_path / "log.jsonl") == []


def test_background_is_left_to_keep_awake(tmp_path, monkeypatch):
    monkeypatch.setattr(re_, "PENDING_DIR", tmp_path / "pending")
    monkeypatch.setattr(re_, "LOG", tmp_path / "log.jsonl")
    payload = {"tool_name": "Bash", "tool_use_id": "t3",
               "tool_input": {"command": "x # estimate: 5m", "run_in_background": True}}
    re_.pre(payload)
    re_.post(payload)
    assert re_.read_log(tmp_path / "log.jsonl") == []
    assert not (tmp_path / "pending").exists()


def test_pre_prints_ratio_line(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(re_, "PENDING_DIR", tmp_path / "pending")
    log = tmp_path / "log.jsonl"
    monkeypatch.setattr(re_, "LOG", log)
    for _ in range(3):
        re_.record("Bash", True, "x # estimate: 10m", 720, path=log)
    re_.pre({"tool_name": "Bash", "tool_use_id": "t4", "tool_input": {"command": "y # estimate: 30m"}})
    out = json.loads(capsys.readouterr().out)
    assert "about 36 min" in out["hookSpecificOutput"]["additionalContext"]
