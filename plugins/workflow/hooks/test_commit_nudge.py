import importlib.util
import subprocess
from pathlib import Path

_spec = importlib.util.spec_from_file_location("commit_nudge", Path(__file__).with_name("commit_nudge.py"))
assert _spec and _spec.loader
commit_nudge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(commit_nudge)


def config_repo(path: Path) -> Path:
    (path / "plugins" / "workflow").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    return path


def test_commit_naming_plugins_gets_the_reminder(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    assert commit_nudge.needs_reminder("git add plugins/workflow/x && git commit -m y", str(repo))


def test_adding_the_plugins_folder_without_a_slash_gets_the_reminder(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    assert commit_nudge.needs_reminder("git add plugins && git commit -m y", str(repo))


def test_commit_with_staged_plugin_files_gets_the_reminder(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    (repo / "plugins" / "workflow" / "a.md").write_text("x")
    subprocess.run(["git", "-C", str(repo), "add", "plugins"], check=True)
    assert commit_nudge.needs_reminder("git commit -m y", str(repo))


def test_commit_of_other_files_gets_nothing(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    (repo / "README.md").write_text("x")
    subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
    assert not commit_nudge.needs_reminder("git commit -m y", str(repo))


def test_other_git_commands_get_nothing(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    assert not commit_nudge.needs_reminder("git status plugins/", str(repo))


def test_a_repo_without_the_plugin_folder_gets_nothing(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    assert not commit_nudge.needs_reminder("git commit -m plugins/", str(tmp_path))


def test_cd_in_the_command_picks_the_repo(tmp_path: Path) -> None:
    repo = config_repo(tmp_path / "cfg")
    other = tmp_path / "other"
    other.mkdir()
    cmd = f'cd "{repo}" && git add plugins/workflow && git commit -m y'
    assert commit_nudge.needs_reminder(cmd, str(other))
