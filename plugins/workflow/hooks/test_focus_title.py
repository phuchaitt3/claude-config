import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("focus_title", Path(__file__).with_name("focus_title.py"))
assert _spec and _spec.loader
focus_title = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(focus_title)

CWD = "/work/myproj"


@pytest.mark.parametrize(
    "prompt",
    ["focus mode", "Focus Mode", "  talk mode please", "/focus", "/talk", "conversation chat"],
)
def test_focus_start_sets_the_title(prompt: str) -> None:
    assert focus_title.title_for(prompt, CWD, "") == "focus-myproj"


def test_focus_start_replaces_a_repo_title() -> None:
    assert focus_title.title_for("/focus", CWD, "myproj-4d") == "focus-myproj"


@pytest.mark.parametrize(
    "prompt",
    ["fix the focus mode bug", "what is focus mode?", "refocus", "/focused", ""],
)
def test_other_prompts_leave_a_titled_chat_alone(prompt: str) -> None:
    assert focus_title.title_for(prompt, CWD, "myproj-4d", "4d4dec") is None


def test_first_prompt_of_an_untitled_chat_gets_the_label_and_id() -> None:
    assert focus_title.title_for("fix the bug", CWD, "", "4d4dec") == "myproj-4d"


def test_a_user_rename_is_kept() -> None:
    assert focus_title.title_for("fix the bug", CWD, "my-own-name", "4d4dec") is None


def test_a_chat_already_named_focus_is_left_alone() -> None:
    assert focus_title.title_for("focus mode", CWD, "focus-c9c10b") is None


def test_a_worktree_folder_becomes_the_suffix() -> None:
    assert focus_title.title_for("/focus", "/work/myproj-35", "") == "focus-myproj-35"


def test_empty_folder_falls_back() -> None:
    assert focus_title.title_for("/focus", "", "") == "focus-chat"


def _layout(tmp_path: Path) -> Path:
    repo = tmp_path / "myrepo"
    (repo / "main").mkdir(parents=True)
    (repo / "12-fix-login").mkdir()
    return repo


def test_main_checkout_gets_the_repo_name(tmp_path: Path) -> None:
    repo = _layout(tmp_path)
    assert focus_title.title_for("hi", str(repo / "main"), "", "4d4dec") == "myrepo-main-4d"
    assert focus_title.title_for("/focus", str(repo / "main"), "") == "focus-myrepo-main"


def test_worktree_beside_main_gets_the_repo_name(tmp_path: Path) -> None:
    repo = _layout(tmp_path)
    assert focus_title.folder_label(str(repo / "12-fix-login")) == "myrepo-12-fix-login"


def test_folder_outside_the_layout_keeps_its_name(tmp_path: Path) -> None:
    (tmp_path / "claude-config").mkdir()
    assert focus_title.folder_label(str(tmp_path / "claude-config")) == "claude-config"
