import importlib.util
from datetime import date
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "data_ready_check", Path(__file__).with_name("data_ready_check.py"))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

EARLY = date(2026, 11, 20)
LATE = date(2026, 11, 27)


def dirs(tmp_path):
    cache, gpu = tmp_path / "cache", tmp_path / "gpu"
    (cache / "keep_awake").mkdir(parents=True)
    gpu.mkdir()
    return cache, gpu


def test_silent_when_no_condition_holds(tmp_path):
    cache, gpu = dirs(tmp_path)
    (cache / "sessionstart.log").write_text("x source=startup\nx source=clear\n")
    assert m.run({}, EARLY, cache, gpu) is None


def test_clear_starts_threshold(tmp_path):
    cache, gpu = dirs(tmp_path)
    (cache / "sessionstart.log").write_text("a source=clear\n" * 3)
    out = m.run({}, EARLY, cache, gpu)
    assert "#5 has enough data" in out and "3 /clear starts" in out


def test_trial_date_reminder(tmp_path):
    cache, gpu = dirs(tmp_path)
    assert "#15" in m.run({}, LATE, cache, gpu)


def test_thermal_alert(tmp_path):
    cache, gpu = dirs(tmp_path)
    (gpu / "events.jsonl").write_text('{"event": "thermal_stopped", "pid": 1}\n')
    assert "#24" in m.run({}, EARLY, cache, gpu)


def test_hold_miss_rate_needs_enough_holds_and_over_five_percent(tmp_path):
    cache, gpu = dirs(tmp_path)
    log = cache / "keep_awake" / "holder.log"
    log.write_text("holding for Bash shell 1\n" * 40 + "no Bash shell found in 90 s\n" * 5)
    assert m.run({}, EARLY, cache, gpu) is None  # 45 holds: too few
    log.write_text("holding for Bash shell 1\n" * 100 + "no Bash shell found in 90 s\n" * 4)
    assert m.run({}, EARLY, cache, gpu) is None  # 4%
    log.write_text("holding for Bash shell 1\n" * 100 + "no Bash shell found in 90 s\n" * 6)
    assert "#21" in m.run({}, EARLY, cache, gpu)


def test_once_per_day_per_issue(tmp_path):
    cache, gpu = dirs(tmp_path)
    assert "#15" in m.run({}, LATE, cache, gpu)
    assert m.run({}, LATE, cache, gpu) is None
    assert "#15" in m.run({}, date(2026, 11, 28), cache, gpu)


def test_only_user_prompt_event():
    assert m.EVENTS == {"UserPromptSubmit"}
