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


SYS_OK = ("C:", 100.0, 476.0, True)


def test_disk_silent_when_there_is_room() -> None:
    _, text = load_watch.decide_disk({}, 1000.0, [SYS_OK, ("D:", 200.0, 931.0, False)])
    assert text == ""


def test_system_drive_warns_below_the_absolute_floor_even_at_a_good_share() -> None:
    _, text = load_watch.decide_disk({}, 1000.0, [("C:", 9.0, 40.0, True)])  # 22% free, 9 GB
    assert "C: has 9.0 GB free of 40 GB" in text and "Never delete" in text


def test_system_drive_warns_below_ten_percent() -> None:
    _, text = load_watch.decide_disk({}, 1000.0, [("C:", 40.0, 476.0, True)])  # 8.4% free
    assert "C:" in text


def test_other_drive_has_no_absolute_floor() -> None:
    _, text = load_watch.decide_disk({}, 1000.0, [("D:", 8.0, 64.0, False)])  # 12.5% free, 8 GB
    assert text == ""
    _, text = load_watch.decide_disk({}, 1000.0, [("D:", 50.0, 931.0, False)])  # 5.4% free
    assert "D: has 50.0 GB free" in text


def test_disk_told_once_per_drive_per_window() -> None:
    drives = [("C:", 5.0, 476.0, True), ("D:", 20.0, 931.0, False)]
    state, text = load_watch.decide_disk({}, 1000.0, drives)
    assert "C:" in text and "D:" in text
    state, again = load_watch.decide_disk(state, 1200.0, drives)
    assert again == ""
    _, later = load_watch.decide_disk(state, 1000.0 + load_watch.TELL_EVERY_S, drives)
    assert "C:" in later
    # a drive that newly goes low is told at once, even inside the other drive's window
    state, _ = load_watch.decide_disk({}, 1000.0, [("C:", 5.0, 476.0, True)])
    _, text = load_watch.decide_disk(state, 1100.0, drives)
    assert "D:" in text and "C:" not in text


def test_disk_state_does_not_disturb_the_load_state() -> None:
    state, _ = load_watch.decide({}, 1000.0, 1000.0, TOTAL, None)
    state, _ = load_watch.decide_disk(state, 1000.0, [("C:", 1.0, 476.0, True)])
    assert state["told"] == 1000.0 and "C:" in state["told_disk"]


def test_disk_drives_reports_the_system_drive_and_survives_a_bad_drive(monkeypatch) -> None:
    monkeypatch.setenv("SystemDrive", "C:")
    calls = []

    def fake(path):
        calls.append(path)
        if path.startswith("Z"):
            raise OSError("no such drive")
        return type("U", (), {"free": 5 * 2**30, "total": 50 * 2**30})()

    monkeypatch.setattr(load_watch.shutil, "disk_usage", fake)
    monkeypatch.setattr(load_watch.os, "getcwd", lambda: "Z:\\work")
    drives = load_watch.disk_drives()
    assert drives == [("C:", 5.0, 50.0, True)] and calls == ["C:\\", "Z:\\"]
