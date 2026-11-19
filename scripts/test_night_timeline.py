import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "night_timeline", Path(__file__).with_name("night_timeline.py"))
nt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nt)

LO = datetime(2026, 11, 18, 11, 0, tzinfo=timezone.utc)
HI = datetime(2026, 11, 19, 3, 0, tzinfo=timezone.utc)


def build(tmp_path):
    claude, gpu = tmp_path / "claude", tmp_path / "gpu"
    (claude / "jobs" / "abc").mkdir(parents=True)
    (claude / "projects" / "p1").mkdir(parents=True)
    gpu.mkdir()
    (claude / "daemon.log").write_text(
        "[2026-11-18T20:12:45.077Z] [bg] bg retire 01b7f2be: settled, idle 60m [low memory]\n"
        "[2026-11-18T20:12:46.000Z] [bg] auth: scheduling proactive refresh in 5106s\n"
        "[2026-11-18T21:45:50.369Z] [supervisor] shutting down (cause=idle_exit)\n"
        "[2026-11-10T21:45:50.369Z] [supervisor] shutting down (cause=old)\n", encoding="utf-8")
    (gpu / "events.jsonl").write_text(
        json.dumps({"ts": "2026-11-19T01:31:24+07:00", "event": "start", "resource": "gpu", "purpose": "run"}) + "\n"
        + json.dumps({"ts": "2026-11-19T01:32:00+07:00", "event": "clock_cap_left_on"}) + "\n", encoding="utf-8")
    (gpu / "thermal.jsonl").write_text(
        json.dumps({"ts": "2026-11-19T01:36:00+07:00", "event": "sample", "mem_phys_free_gb": 2.1,
                    "mem_free_gb": 7.5, "top_mem_mb": {"python.exe": 9000}}) + "\n"
        + json.dumps({"ts": "2026-11-19T01:37:00+07:00", "event": "low_memory", "mem_phys_free_gb": 2.4,
                      "top_mem_mb": {"python.exe": 8000}}) + "\n"
        + json.dumps({"ts": "2026-11-19T01:38:00+07:00", "event": "sample", "mem_phys_free_gb": 5.0}) + "\n",
        encoding="utf-8")
    (claude / "projects" / "p1" / "aaaaaaaa-1.jsonl").write_text(
        json.dumps({"timestamp": "2026-11-18T18:38:00.000Z",
                    "message": {"content": "task " + nt.KILL_TEXT}}) + "\n", encoding="utf-8")
    (claude / "jobs" / "abc" / "state.json").write_text(
        json.dumps({"name": "selfdrive-x", "state": "done", "detail": "merged",
                    "updatedAt": "2026-11-18T21:45:45.349Z"}), encoding="utf-8")
    return claude, gpu


def test_merged_sorted_and_filtered(tmp_path):
    claude, gpu = build(tmp_path)
    rows = nt.collect(claude, gpu, LO, HI)
    text = [f"{s}:{t}" for _, s, t in rows]
    assert [r[0] for r in rows] == sorted(r[0] for r in rows)
    assert any("retire 01b7f2be" in t and "[low memory]" in t for t in text)
    assert any(t.startswith("daemon:shutting down (cause=idle_exit)") for t in text)
    assert not any("cause=old" in t or "proactive refresh" in t for t in text)
    assert any(t.startswith("lock:start resource=gpu") for t in text)
    assert not any("clock_cap_left_on" in t for t in text)
    assert sum(t.startswith("thermal:low_memory") for t in text) == 1
    assert any("lowest mem_phys_free_gb in window = 2.1" in t and "python.exe" in t for t in text)
    assert any(t.startswith("harness:") for t in text)
    assert any("selfdrive-x" in t and "state=done" in t for t in text)


def test_window_excludes_outside(tmp_path):
    claude, gpu = build(tmp_path)
    assert nt.collect(claude, gpu, datetime(2026, 12, 1, tzinfo=timezone.utc),
                      datetime(2026, 12, 2, tzinfo=timezone.utc)) == []


def test_missing_sources_are_silent(tmp_path):
    assert nt.collect(tmp_path / "none", tmp_path / "none2", LO, HI) == []
