import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("chat_title", Path(__file__).with_name("chat_title.py"))
assert _spec and _spec.loader
chat_title = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(chat_title)


def _layout(tmp_path: Path) -> Path:
    repo = tmp_path / "myrepo"
    (repo / "main").mkdir(parents=True)
    (repo / "12-fix-login").mkdir()
    return repo


def test_main_checkout_gets_the_repo_name(tmp_path: Path) -> None:
    repo = _layout(tmp_path)
    assert chat_title.folder_label(str(repo / "main")) == "myrepo-main"


def test_worktree_beside_main_gets_the_repo_name(tmp_path: Path) -> None:
    repo = _layout(tmp_path)
    assert chat_title.folder_label(str(repo / "12-fix-login")) == "myrepo-12-fix-login"


def test_folder_outside_the_layout_keeps_its_name(tmp_path: Path) -> None:
    (tmp_path / "claude-config").mkdir()
    assert chat_title.folder_label(str(tmp_path / "claude-config")) == "claude-config"


def test_empty_folder_falls_back() -> None:
    assert chat_title.folder_label("") == "chat"


def test_new_session_gets_label_and_id(tmp_path: Path) -> None:
    repo = _layout(tmp_path)
    assert chat_title.title_for("startup", str(repo / "main"), "4d4dec-x") == "myrepo-main-4d"


def test_other_sources_keep_their_title(tmp_path: Path) -> None:
    repo = _layout(tmp_path)
    for source in ("resume", "clear", "compact", ""):
        assert chat_title.title_for(source, str(repo / "main"), "4d4dec") is None


def test_missing_session_id_gives_the_label_alone(tmp_path: Path) -> None:
    repo = _layout(tmp_path)
    assert chat_title.title_for("startup", str(repo / "main"), "") == "myrepo-main"
