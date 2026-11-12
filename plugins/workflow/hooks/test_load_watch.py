import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("load_watch", Path(__file__).with_name("load_watch.py"))
assert _spec and _spec.loader
load_watch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(load_watch)

TOTAL = 16384.0


def test_silent_when_the_machine_is_fine() -> None:
    _, text = load_watch.decide({}, 1000.0, 8000.0, TOTAL, 30.0)
    assert text == ""


def test_low_memory_is_told() -> None:
    _, text = load_watch.decide({}, 1000.0, 1500.0, TOTAL, 10.0)
    assert "free memory 1.5 GB of 16 GB" in text and "heavy local job" in text


def test_low_memory_by_share_on_a_small_machine() -> None:
    _, text = load_watch.decide({}, 1000.0, 3000.0, 32768.0, None)
    assert "free memory" in text


def test_high_cpu_is_told_and_unknown_cpu_is_not() -> None:
    _, text = load_watch.decide({}, 1000.0, 8000.0, TOTAL, 95.0)
    assert "CPU 95% busy" in text
    _, quiet = load_watch.decide({}, 1000.0, 8000.0, TOTAL, None)
    assert quiet == ""


def test_told_once_per_window() -> None:
    state, text = load_watch.decide({}, 1000.0, 1000.0, TOTAL, None)
    assert text
    state, again = load_watch.decide(state, 1200.0, 1000.0, TOTAL, None)
    assert again == ""
    _, later = load_watch.decide(state, 1000.0 + load_watch.TELL_EVERY_S, 1000.0, TOTAL, None)
    assert later


def test_cpu_percent_from_two_samples() -> None:
    assert load_watch.cpu_percent(None, (50, 100)) is None
    assert load_watch.cpu_percent([50, 100], (150, 200)) == 100.0
    assert load_watch.cpu_percent([50, 100], (75, 200)) == 25.0
