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


def test_other_programs_are_never_touched_by_the_search_rule() -> None:
    orphans, runners = stray_procs.classify([proc(10, 999, "python.exe", 600)], NOW.timestamp())
    assert not orphans and not runners


def run_proc(pid: int, parent: int, name: str, minutes_old: float, command: str) -> dict:
    return {**proc(pid, parent, name, minutes_old), "CommandLine": command}


def runners(procs: list[dict], protected: set[int] | None = None):
    return stray_procs.classify_runners(procs, NOW.timestamp(), protected or set())


PYTEST = "python.exe -m pytest scripts -q"


def test_orphaned_test_run_is_ended() -> None:
    kill, report = runners([run_proc(10, 999, "python.exe", 45, PYTEST)])
    assert [p["ProcessId"] for p in kill] == [10] and not report
    kill, _ = runners([run_proc(11, 999, "node.exe", 45, "node node_modules/jest/bin/jest.js")])
    assert [p["ProcessId"] for p in kill] == [11]


def test_young_test_run_or_one_with_a_live_parent_is_left_alone() -> None:
    assert runners([run_proc(10, 999, "python.exe", 20, PYTEST)]) == ([], [])
    parent = proc(1, 0, "bash.exe", 600)
    assert runners([parent, run_proc(10, 1, "python.exe", 600, PYTEST)]) == ([], [])


def test_guarded_jobs_are_never_touched_whatever_their_age() -> None:
    wrapped = r"python C:\Users\x\claude-config\scripts\gpu_run.py run -- python -m pytest"
    assert runners([run_proc(10, 999, "python.exe", 900, wrapped)]) == ([], [])
    assert runners([run_proc(10, 999, "python.exe", 900, "python keepawake.ps1 train.py")]) == ([], [])


def test_lock_holder_and_its_children_are_never_touched() -> None:
    child = run_proc(11, 10, "python.exe", 300, PYTEST)
    holder = run_proc(10, 999, "python.exe", 300, PYTEST)
    assert runners([holder, child], {10}) == ([], [])
    kill, _ = runners([holder, child], set())
    assert [p["ProcessId"] for p in kill] == [10]  # the child's parent is alive; only the holder is parentless


def test_a_reused_parent_pid_counts_as_parentless() -> None:
    younger_parent = run_proc(1, 0, "explorer.exe", 5, "explorer.exe")  # pid 1 was reused 5 minutes ago
    kill, _ = runners([younger_parent, run_proc(10, 1, "python.exe", 90, PYTEST)])
    assert [p["ProcessId"] for p in kill] == [10]


def test_unknown_parentless_python_is_reported_not_ended() -> None:
    kill, report = runners([run_proc(10, 999, "python.exe", 200, "python train.py --epochs 50")])
    assert not kill and [p["ProcessId"] for p in report] == [10]
    assert runners([run_proc(10, 999, "python.exe", 90, "python train.py")]) == ([], [])  # under 2 h


def test_servers_editors_and_unrelated_programs_are_not_even_reported() -> None:
    for command in (
        r"node C:\Users\x\.vscode\extensions\a\server.js",
        "python -m uvicorn app:app --reload",
        "python -m http.server 8000",
        "python -m jupyter lab",
        "node mcp-server.js",
    ):
        assert runners([run_proc(10, 999, "python.exe" if "python" in command else "node.exe", 600, command)]) == ([], [])
    assert runners([run_proc(10, 999, "chrome.exe", 600, "chrome.exe")]) == ([], [])


def test_pytest_word_must_stand_alone() -> None:
    kill, _ = runners([run_proc(10, 999, "python.exe", 90, r"python C:\x\.pytest_cache\run.py")])
    assert not kill
    kill, _ = runners([run_proc(10, 999, "python.exe", 90, r"python C:\x\my-pytest-plugin\run.py")])
    assert not kill


def test_main_ends_runner_with_its_tree_logs_it_and_reports_each_unknown_once(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(stray_procs, "CACHE", tmp_path / "cache.json")
    monkeypatch.setattr(stray_procs, "LOG", tmp_path / "stray.log")
    monkeypatch.setattr(stray_procs.sys, "platform", "win32")
    monkeypatch.setattr(stray_procs.time, "time", lambda: NOW.timestamp())
    monkeypatch.setattr(stray_procs, "lock_holders", lambda: set())
    procs = [
        run_proc(10, 999, "python.exe", 45, PYTEST),
        run_proc(20, 999, "python.exe", 300, "python train.py"),
    ]
    monkeypatch.setattr(stray_procs, "list_processes", lambda: procs)
    killed = []
    monkeypatch.setattr(stray_procs, "kill", lambda pid, tree=False: killed.append((pid, tree)) or True)
    stray_procs.main()
    assert killed == [(10, True)]
    out = capsys.readouterr().out
    assert "ended orphaned test run python.exe 10" in out and "no parent, not ended: python.exe 20" in out
    assert "killed python.exe 10" in (tmp_path / "stray.log").read_text(encoding="utf-8")
    # next window: the runner is gone, the unknown process was reported already, so nothing is said
    monkeypatch.setattr(stray_procs.time, "time", lambda: NOW.timestamp() + 700)
    killed.clear()
    monkeypatch.setattr(stray_procs, "list_processes", lambda: procs[1:])
    stray_procs.main()
    assert killed == [] and capsys.readouterr().out == ""
