import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

_spec = importlib.util.spec_from_file_location("stray_procs", Path(__file__).with_name("stray_procs.py"))
assert _spec and _spec.loader
stray_procs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(stray_procs)

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)


def proc(pid: int, parent: int, name: str, minutes_old: float) -> dict:
    started = (NOW - timedelta(minutes=minutes_old)).isoformat()
    return {"ProcessId": pid, "ParentProcessId": parent, "Name": name, "Started": started, "CommandLine": name}


def test_old_search_with_dead_parent_is_an_orphan() -> None:
    orphans, runners = stray_procs.classify([proc(10, 999, "find.exe", 60)], NOW.timestamp())
    assert [p["ProcessId"] for p in orphans] == [10] and not runners


def test_young_search_with_dead_parent_is_left_alone() -> None:
    orphans, runners = stray_procs.classify([proc(10, 999, "find.exe", 5)], NOW.timestamp())
    assert not orphans and not runners


def test_search_with_live_parent_is_only_reported_after_an_hour() -> None:
    parent = proc(1, 0, "bash.exe", 600)
    assert stray_procs.classify([parent, proc(10, 1, "find.exe", 30)], NOW.timestamp()) == ([], [])
    _, runners = stray_procs.classify([parent, proc(10, 1, "find.exe", 90)], NOW.timestamp())
    assert [p["ProcessId"] for p in runners] == [10]


def test_other_programs_are_never_touched() -> None:
    orphans, runners = stray_procs.classify([proc(10, 999, "python.exe", 600)], NOW.timestamp())
    assert not orphans and not runners
