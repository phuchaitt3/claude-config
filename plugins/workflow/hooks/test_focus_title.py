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


@pytest.mark.parametrize(
    "prompt",
    ["fix the focus mode bug", "what is focus mode?", "refocus", "/focused", ""],
)
def test_other_prompts_are_left_alone(prompt: str) -> None:
    assert focus_title.title_for(prompt, CWD, "") is None


def test_a_chat_already_named_focus_is_left_alone() -> None:
    assert focus_title.title_for("focus mode", CWD, "focus-c9c10b") is None


def test_a_worktree_folder_becomes_the_suffix() -> None:
    assert focus_title.title_for("/focus", "/work/myproj-35", "") == "focus-myproj-35"


def test_empty_folder_falls_back() -> None:
    assert focus_title.title_for("/focus", "", "") == "focus-chat"


def test_main_checkout_title_names_the_repo(tmp_path) -> None:
    (tmp_path / "myrepo" / "main").mkdir(parents=True)
    assert focus_title.title_for("/focus", str(tmp_path / "myrepo" / "main"), "") == "focus-myrepo-main"
