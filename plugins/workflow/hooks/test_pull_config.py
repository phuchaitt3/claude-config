import importlib.util
import subprocess
from pathlib import Path

_spec = importlib.util.spec_from_file_location("pull_config", Path(__file__).with_name("pull_config.py"))
assert _spec and _spec.loader
pull_config = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pull_config)


def git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def make_pair(tmp_path: Path) -> tuple[Path, Path]:
    origin, clone = tmp_path / "origin", tmp_path / "clone"
    origin.mkdir()
    git("init", "-q", "-b", "main", cwd=origin)
    git("config", "user.email", "t@t", cwd=origin)
    git("config", "user.name", "t", cwd=origin)
    (origin / "a.txt").write_text("1")
    git("add", "a.txt", cwd=origin)
    git("commit", "-q", "-m", "one", cwd=origin)
    subprocess.run(["git", "clone", "-q", str(origin), str(clone)], check=True)
    return origin, clone


def test_due_respects_the_interval(tmp_path: Path) -> None:
    stamp = tmp_path / "stamp"
    assert pull_config.due(1000.0, stamp) is True  # no stamp yet
    stamp.touch()
    now = stamp.stat().st_mtime
    assert pull_config.due(now + 60, stamp) is False
    assert pull_config.due(now + 31 * 60, stamp) is True


def test_pull_fast_forwards_a_clean_clone(tmp_path: Path) -> None:
    origin, clone = make_pair(tmp_path)
    (origin / "b.txt").write_text("2")
    git("add", "b.txt", cwd=origin)
    git("commit", "-q", "-m", "two", cwd=origin)
    assert pull_config.pull(clone) is True
    assert (clone / "b.txt").read_text() == "2"


def test_diverged_clone_is_left_alone(tmp_path: Path) -> None:
    origin, clone = make_pair(tmp_path)
    git("config", "user.email", "t@t", cwd=clone)
    git("config", "user.name", "t", cwd=clone)
    (origin / "b.txt").write_text("remote")
    git("add", "b.txt", cwd=origin)
    git("commit", "-q", "-m", "remote", cwd=origin)
    (clone / "c.txt").write_text("local")
    git("add", "c.txt", cwd=clone)
    git("commit", "-q", "-m", "local", cwd=clone)
    assert pull_config.pull(clone) is False
    assert not (clone / "b.txt").exists() and (clone / "c.txt").read_text() == "local"


def test_missing_repo_is_a_quiet_no(tmp_path: Path) -> None:
    assert pull_config.pull(tmp_path / "nope") is False
