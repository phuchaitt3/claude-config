import importlib.util
import subprocess
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "main_checkout", Path(__file__).with_name("main_checkout.py")
)
assert _spec and _spec.loader
main_checkout = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(main_checkout)


def sh(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=cwd,
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def commit(cwd: Path, name: str) -> None:
    (cwd / name).write_text(name)
    sh(cwd, "add", name)
    sh(cwd, "commit", "-q", "-m", name)


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A main checkout with a handoff folder, its origin, and a second clone that pushes to it."""
    sh(tmp_path, "init", "-q", "--bare", "-b", "main", "origin.git")
    main = tmp_path / "proj"
    main.mkdir()
    sh(main, "init", "-q", "-b", "main")
    commit(main, "a")
    sh(main, "remote", "add", "origin", str(tmp_path / "origin.git"))
    sh(main, "push", "-q", "-u", "origin", "main")
    sh(main, "remote", "set-head", "origin", "main")
    (main / ".git" / "info" / "exclude").write_text(".handoff/\n")
    (main / ".handoff").mkdir()
    sh(tmp_path, "clone", "-q", str(tmp_path / "origin.git"), "other")
    return main


def land_on_origin(main: Path, name: str) -> None:
    """Simulate a merge on GitHub: a commit reaches origin/main from somewhere else."""
    other = main.parent / "other"
    sh(other, "pull", "-q")
    commit(other, name)
    sh(other, "push", "-q")


def test_refresh_fast_forwards_the_default_branch(repo: Path) -> None:
    land_on_origin(repo, "b")
    assert main_checkout.refresh(repo) is None
    assert (repo / "b").exists()


def test_refresh_switches_back_from_a_detached_head(repo: Path) -> None:
    land_on_origin(repo, "b")
    sh(repo, "checkout", "-q", "--detach", "HEAD")
    assert main_checkout.refresh(repo) is None
    assert sh(repo, "branch", "--show-current") == "main" and (repo / "b").exists()


def test_refresh_warns_and_leaves_uncommitted_work(repo: Path) -> None:
    land_on_origin(repo, "b")
    (repo / "a").write_text("edited")
    warning = main_checkout.refresh(repo)
    assert warning and "uncommitted" in warning and "1 commits behind" in warning
    assert (repo / "a").read_text() == "edited" and not (repo / "b").exists()


def test_refresh_warns_on_an_unmerged_branch(repo: Path) -> None:
    sh(repo, "checkout", "-q", "-b", "feat/x")
    commit(repo, "c")
    warning = main_checkout.refresh(repo)
    assert warning and "feat/x" in warning
    assert sh(repo, "branch", "--show-current") == "feat/x"


@pytest.mark.parametrize(
    "command",
    ["git commit -m x", "git checkout feat/x", "git switch -c feat/y", "git checkout -b main",
     "git reset --hard HEAD~1", "git pull", "git rebase origin/main", "git merge origin/main"],
)
def test_guard_refuses_git_work_in_the_main_checkout(repo: Path, command: str) -> None:
    reason = main_checkout.check(command, str(repo))
    assert reason and "worktree" in reason


@pytest.mark.parametrize(
    "command",
    ["git status", "git fetch origin", "git switch main", "git checkout main",
     "git pull --ff-only", "git show origin/main:a", "git worktree add ../w -b feat/x origin/main",
     'echo "git commit -m x"'],
)
def test_guard_allows_reads_and_returning_to_main(repo: Path, command: str) -> None:
    assert main_checkout.check(command, str(repo)) is None


def test_guard_allows_git_work_in_a_worktree_and_in_the_handoff_repo(repo: Path) -> None:
    sh(repo, "worktree", "add", "-q", str(repo.parent / "proj-1"), "-b", "feat/x", "origin/main")
    assert main_checkout.check("git commit -m x", str(repo.parent / "proj-1")) is None
    sh(repo / ".handoff", "init", "-q")
    assert main_checkout.check("git -C .handoff commit -m x", str(repo)) is None
    assert main_checkout.check("cd .handoff && git pull --rebase", str(repo)) is None


def test_guard_ignores_projects_without_a_handoff_folder(repo: Path) -> None:
    (repo / ".handoff").rmdir()
    assert main_checkout.check("git commit -m x", str(repo)) is None


def test_prompt_shows_a_warning_once_per_session(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(main_checkout, "CACHE", tmp_path / "cache")
    monkeypatch.setattr(main_checkout, "spawn_detached", lambda args: None)
    (repo / "a").write_text("edited")
    main_checkout.run_refresh(repo)
    payload = {"cwd": str(repo), "session_id": "s1"}
    first = main_checkout.on_prompt(payload, "UserPromptSubmit", 1e10)
    assert first and "uncommitted" in first
    assert main_checkout.on_prompt(payload, "UserPromptSubmit", 1e10) is None
    assert main_checkout.on_prompt({**payload, "session_id": "s2"}, "UserPromptSubmit", 1e10)


def test_prompt_starts_a_refresh_only_when_due(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(main_checkout, "CACHE", tmp_path / "cache")
    started: list[list[str]] = []
    monkeypatch.setattr(main_checkout, "spawn_detached", started.append)
    payload = {"cwd": str(repo), "session_id": "s1"}
    import time

    main_checkout.on_prompt(payload, "SessionStart", time.time())
    main_checkout.on_prompt(payload, "UserPromptSubmit", time.time())
    assert len(started) == 1 and started[0][1:] == ["refresh", str(repo)]
