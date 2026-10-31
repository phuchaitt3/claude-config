import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

_spec = importlib.util.spec_from_file_location("plugin_notice", Path(__file__).with_name("plugin_notice.py"))
assert _spec and _spec.loader
plugin_notice = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(plugin_notice)

TZ = timezone(timedelta(hours=7))
T0 = datetime(2026, 10, 31, 12, 0, tzinfo=TZ)
CRITICAL = ("0.7.3", T0 + timedelta(hours=2), "a wrong merge gate")


def test_session_start_records_the_start_and_says_nothing() -> None:
    state, text = plugin_notice.decide("SessionStart", {}, CRITICAL, T0)
    assert state["start"] == T0.isoformat() and text == ""


def test_session_older_than_the_update_is_told_once() -> None:
    state, _ = plugin_notice.decide("SessionStart", {}, CRITICAL, T0)
    now = T0 + timedelta(hours=3)
    state, text = plugin_notice.decide("UserPromptSubmit", state, CRITICAL, now)
    assert "0.7.3" in text and "a wrong merge gate" in text and "/reload-plugins" in text
    _, again = plugin_notice.decide("UserPromptSubmit", state, CRITICAL, now)
    assert again == ""


def test_session_started_after_the_update_is_not_told() -> None:
    state, _ = plugin_notice.decide("SessionStart", {}, CRITICAL, T0 + timedelta(hours=2, minutes=1))
    _, text = plugin_notice.decide("UserPromptSubmit", state, CRITICAL, T0 + timedelta(hours=5))
    assert text == ""


def test_a_session_the_hook_never_saw_start_counts_from_its_first_prompt() -> None:
    state, text = plugin_notice.decide("UserPromptSubmit", {}, CRITICAL, T0 + timedelta(hours=3))
    assert text == "" and "start" in state


def test_a_later_critical_update_is_announced_again() -> None:
    state, _ = plugin_notice.decide("SessionStart", {}, CRITICAL, T0)
    state, _ = plugin_notice.decide("UserPromptSubmit", state, CRITICAL, T0 + timedelta(hours=3))
    newer = ("0.8.0", T0 + timedelta(hours=4), "a new push gate")
    _, text = plugin_notice.decide("UserPromptSubmit", state, newer, T0 + timedelta(hours=5))
    assert "0.8.0" in text


def test_no_critical_file_means_no_notice() -> None:
    state, _ = plugin_notice.decide("SessionStart", {}, None, T0)
    _, text = plugin_notice.decide("UserPromptSubmit", state, None, T0 + timedelta(hours=9))
    assert text == ""


def test_read_critical_parses_the_file(tmp_path: Path) -> None:
    path = tmp_path / "critical.json"
    path.write_text(json.dumps({"version": "1", "since": "2026-10-31T16:17:08+07:00", "why": "x"}))
    version, published, why = plugin_notice.read_critical(path)
    assert (version, why) == ("1", "x") and published.utcoffset() == timedelta(hours=7)


def test_read_critical_rejects_missing_broken_and_naive_times(tmp_path: Path) -> None:
    assert plugin_notice.read_critical(tmp_path / "none.json") is None
    bad = tmp_path / "bad.json"
    bad.write_text("{")
    assert plugin_notice.read_critical(bad) is None
    naive = tmp_path / "naive.json"
    naive.write_text(json.dumps({"version": "1", "since": "2026-10-31T16:17:08"}))
    assert plugin_notice.read_critical(naive) is None


def test_the_shipped_critical_file_is_valid() -> None:
    assert plugin_notice.read_critical() is not None
