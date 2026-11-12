import importlib.util
import json
import os
from pathlib import Path

_spec = importlib.util.spec_from_file_location("skill_nudge", Path(__file__).with_name("skill_nudge.py"))
assert _spec and _spec.loader
skill_nudge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(skill_nudge)

DEAD_PID = 2**22 + 12345  # beyond the usual pid range on both Windows and Linux


def write_session(folder: Path, name: str, session_id: str, pid: int, cwd: str, started: int = 1) -> None:
    folder.mkdir(exist_ok=True)
    (folder / f"{name}.json").write_text(
        json.dumps({"pid": pid, "sessionId": session_id, "cwd": cwd, "startedAt": started}),
        encoding="utf-8",
    )


def test_no_session_files_means_no_peers(tmp_path: Path) -> None:
    assert skill_nudge.other_live_sessions("me", tmp_path / "missing") == []


def test_own_session_is_excluded(tmp_path: Path) -> None:
    write_session(tmp_path, "a", "me-0000", os.getpid(), "d:/repo")
    assert skill_nudge.other_live_sessions("me-0000", tmp_path) == []


def test_live_peer_in_any_repository_is_listed(tmp_path: Path) -> None:
    write_session(tmp_path, "a", "peer01-xxxx", os.getpid(), "d:/other/main")
    assert skill_nudge.other_live_sessions("me-0000", tmp_path) == [("peer01", "d:/other/main")]


def test_dead_process_is_not_a_peer(tmp_path: Path) -> None:
    write_session(tmp_path, "a", "dead01-xxxx", DEAD_PID, "d:/repo")
    assert skill_nudge.other_live_sessions("me-0000", tmp_path) == []


def test_unreadable_file_is_skipped(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{not json", encoding="utf-8")
    write_session(tmp_path, "a", "peer01-xxxx", os.getpid(), "d:/repo")
    assert len(skill_nudge.other_live_sessions("me-0000", tmp_path)) == 1


def test_peers_are_listed_oldest_first(tmp_path: Path) -> None:
    write_session(tmp_path, "a", "newer1-xxxx", os.getpid(), "d:/b", started=20)
    write_session(tmp_path, "b", "older1-xxxx", os.getpid(), "d:/a", started=10)
    prefixes = [p for p, _ in skill_nudge.other_live_sessions("me-0000", tmp_path)]
    assert prefixes == ["older1", "newer1"]


def test_message_names_skill_listagents_and_peers() -> None:
    text = skill_nudge.message([("peer01", "d:/other/main")])
    assert "workflow:multi-chat" in text
    assert "ListAgents" in text
    assert "peer01 in d:/other/main" in text


def test_message_caps_the_list() -> None:
    peers = [(f"p{i:05d}", "d:/r") for i in range(skill_nudge.MAX_LISTED + 3)]
    assert "(and 3 more)" in skill_nudge.message(peers)
