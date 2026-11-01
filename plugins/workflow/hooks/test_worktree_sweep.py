import importlib.util
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "worktree_sweep", Path(__file__).with_name("worktree_sweep.py")
)
assert _spec and _spec.loader
worktree_sweep = importlib.util.module_from_spec(_spec)
sys.modules["worktree_sweep"] = worktree_sweep  # dataclasses look their module up there
_spec.loader.exec_module(worktree_sweep)

NOW = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
LONG_AGO = (NOW - timedelta(days=1)).isoformat().replace("+00:00", "Z")
JUST_NOW = (NOW - timedelta(minutes=30)).isoformat().replace("+00:00", "Z")


def sh(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=cwd,
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def commit(cwd: Path, name: str) -> str:
    (cwd / name).write_text(name)
    sh(cwd, "add", name)
    sh(cwd, "commit", "-q", "-m", name)
    return sh(cwd, "rev-parse", "HEAD")


@pytest.fixture()
def main(tmp_path: Path) -> Path:
    sh(tmp_path, "init", "-q", "--bare", "-b", "main", "origin.git")
    repo = tmp_path / "proj"
    repo.mkdir()
    sh(repo, "init", "-q", "-b", "main")
    commit(repo, "a")
    sh(repo, "remote", "add", "origin", str(tmp_path / "origin.git"))
    sh(repo, "push", "-q", "-u", "origin", "main")
    sh(repo, "remote", "set-head", "origin", "main")
    (repo / ".git" / "info" / "exclude").write_text(".handoff/\nnode_modules/\n.env.local\n")
    (repo / ".handoff").mkdir()
    return repo


def task_worktree(main: Path, name: str) -> tuple[Path, str]:
    """A worktree with one pushed commit, as a chat leaves it after its PR merged."""
    path = main.parent / f"proj-{name}"
    sh(main, "worktree", "add", "-q", str(path), "-b", f"feat/{name}", "origin/main")
    head = commit(path, f"{name}.txt")
    sh(path, "push", "-q", "-u", "origin", f"feat/{name}")
    return path, head


def prs(**merged: tuple[str, str]) -> "worktree_sweep.Prs":
    """branch name (underscore for slash) -> (head oid, mergedAt)."""
    result = worktree_sweep.Prs()
    for i, (key, (oid, at)) in enumerate(merged.items()):
        branch = key.replace("_", "/", 1)
        result.merged[branch] = [{"number": i + 1, "headRefName": branch, "headRefOid": oid,
                                  "mergedAt": at}]
    return result


def run(main: Path, monkeypatch: pytest.MonkeyPatch, found: "worktree_sweep.Prs",
        dry_run: bool = False) -> list[str]:
    monkeypatch.setattr(worktree_sweep, "read_prs", lambda _main: found)
    return worktree_sweep.sweep(main, dry_run=dry_run, now=NOW)


def test_a_clean_merged_worktree_is_removed_and_its_branch_kept(
    main: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, head = task_worktree(main, "x")
    (path / "node_modules").mkdir()
    (path / "node_modules" / "pkg.js").write_text("")
    lines = run(main, monkeypatch, prs(feat_x=(head, LONG_AGO)))
    assert lines[0].startswith("remove ") and not path.exists()
    assert sh(main, "branch", "--list", "feat/x")


def test_files_git_leaves_behind_are_deleted(main: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """On Windows git can unregister a worktree, then fail inside node_modules."""
    path, head = task_worktree(main, "x")
    real_git_ok = worktree_sweep.git_ok

    def partial_remove(args: list[str], cwd: Path, timeout: float = 8) -> bool:
        if args[:2] == ["worktree", "remove"]:
            (path / ".git").unlink()
            sh(main, "worktree", "prune")
            return False
        return real_git_ok(args, cwd, timeout)

    monkeypatch.setattr(worktree_sweep, "git_ok", partial_remove)
    lines = run(main, monkeypatch, prs(feat_x=(head, LONG_AGO)))
    assert lines[0].startswith("remove ") and "left behind" in lines[0] and not path.exists()


def test_a_refused_removal_is_kept(main: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path, head = task_worktree(main, "x")
    real_git_ok = worktree_sweep.git_ok
    monkeypatch.setattr(
        worktree_sweep, "git_ok",
        lambda args, cwd, timeout=8: False if args[:2] == ["worktree", "remove"]
        else real_git_ok(args, cwd, timeout),
    )
    lines = run(main, monkeypatch, prs(feat_x=(head, LONG_AGO)))
    assert lines[0].startswith("keep ") and "refused" in lines[0] and path.exists()


def test_dry_run_changes_nothing(main: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path, head = task_worktree(main, "x")
    lines = run(main, monkeypatch, prs(feat_x=(head, LONG_AGO)), dry_run=True)
    assert lines[0].startswith("remove ") and path.exists()


def test_open_pr_and_recent_merge_are_kept(main: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, head_x = task_worktree(main, "x")
    _, head_y = task_worktree(main, "y")
    found = prs(feat_x=(head_x, LONG_AGO), feat_y=(head_y, JUST_NOW))
    found.open = {"feat/x"}
    lines = run(main, monkeypatch, found)
    assert any("keep" in line and "open PR" in line for line in lines)
    assert any("keep" in line and "merged under" in line for line in lines)


def test_unpushed_commit_is_kept(main: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path, head = task_worktree(main, "x")
    commit(path, "later.txt")
    lines = run(main, monkeypatch, prs(feat_x=(head, LONG_AGO)))
    assert lines[0].startswith("keep ") and "commits not in" in lines[0] and path.exists()


@pytest.mark.parametrize(
    ("name", "reason"),
    [("notes.txt", "untracked"), (".env.local", "may not rebuild")],
)
def test_untracked_and_irreplaceable_ignored_files_are_kept(
    main: Path, monkeypatch: pytest.MonkeyPatch, name: str, reason: str
) -> None:
    path, head = task_worktree(main, "x")
    (path / name).write_text("keep me")
    lines = run(main, monkeypatch, prs(feat_x=(head, LONG_AGO)))
    assert lines[0].startswith("keep ") and reason in lines[0] and (path / name).exists()


def test_locked_and_unmerged_worktrees_are_kept(
    main: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, head = task_worktree(main, "x")
    task_worktree(main, "y")
    sh(main, "worktree", "lock", str(path))
    lines = run(main, monkeypatch, prs(feat_x=(head, LONG_AGO)))
    assert any("locked" in line for line in lines)
    assert any("no merged PR" in line for line in lines)


def test_session_start_reports_removals_once(
    main: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(worktree_sweep, "CACHE", tmp_path / "cache")
    monkeypatch.setattr(worktree_sweep, "spawn_detached", lambda args: None)
    _, head = task_worktree(main, "x")
    monkeypatch.setattr(worktree_sweep, "read_prs", lambda _main: prs(feat_x=(head, LONG_AGO)))
    monkeypatch.setattr(worktree_sweep, "sweep",
                        lambda m, dry_run: ["remove /p [feat/x] PR #1 merged"])
    worktree_sweep.run_sweep(main)
    note = worktree_sweep.on_session_start({"cwd": str(main)}, 1e10)
    assert note and "removed 1" in note
    assert worktree_sweep.on_session_start({"cwd": str(main)}, 1e10) is None
