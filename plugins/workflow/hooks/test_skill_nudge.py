import importlib.util
import subprocess
from pathlib import Path

_spec = importlib.util.spec_from_file_location("skill_nudge", Path(__file__).with_name("skill_nudge.py"))
assert _spec and _spec.loader
skill_nudge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(skill_nudge)


def init_repo(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)


def test_handoff_dir_is_found(tmp_path: Path) -> None:
    (tmp_path / ".handoff").mkdir()
    assert skill_nudge.handoff_folder(tmp_path) == tmp_path / ".handoff"


def test_inbox_in_root_counts(tmp_path: Path) -> None:
    (tmp_path / "INBOX.md").write_text("x")
    assert skill_nudge.handoff_folder(tmp_path) == tmp_path


def test_plain_repo_has_no_handoff_folder(tmp_path: Path) -> None:
    assert skill_nudge.handoff_folder(tmp_path) is None


def test_main_checkout_from_a_subfolder(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    sub = repo / "a"
    sub.mkdir()
    assert skill_nudge.main_checkout(sub) == repo.resolve()


def test_main_checkout_outside_a_repo_is_none(tmp_path: Path) -> None:
    assert skill_nudge.main_checkout(tmp_path) is None


def test_message_names_the_skill_and_folder(tmp_path: Path) -> None:
    text = skill_nudge.message(tmp_path / ".handoff")
    assert "workflow:multi-chat" in text
    assert ".handoff" in text
