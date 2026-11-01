import importlib.util
import subprocess
from pathlib import Path

_spec = importlib.util.spec_from_file_location("tag_check", Path(__file__).with_name("tag_check.py"))
assert _spec and _spec.loader
tag_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tag_check)


def config_repo(path: Path) -> Path:
    (path / "plugins" / "workflow").mkdir(parents=True)
    (path / "standards").mkdir()
    (path / "standards" / "real-topic.md").write_text("x")
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    return path


def stage(repo: Path, name: str, text: str) -> None:
    (repo / name).write_text(text)
    subprocess.run(["git", "-C", str(repo), "add", name], check=True)


def test_tag_to_an_existing_entry_passes(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "(standard: standards/real-topic, checked 2026-11-01)\n")
    assert tag_check.check("git commit -m y", str(repo)) == []


def test_tag_to_a_missing_entry_is_reported(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "(standard: standards/ghost-topic, checked 2026-11-01)\n")
    assert tag_check.check("git commit -m y", str(repo)) == ["ghost-topic"]


def test_a_url_with_standards_in_its_path_is_not_a_reference(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "[GDS](https://gds-way.example.uk/standards/architecture-decisions.html)\n")
    assert tag_check.check("git commit -m y", str(repo)) == []


def test_the_placeholder_in_the_template_is_ignored(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "one file per topic, `standards/<topic>.md`, tag standards/topic\n")
    assert tag_check.check("git commit -m y", str(repo)) == []


def test_only_added_lines_count(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "(standard: standards/ghost-topic, checked 2026-11-01)\n")
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-q", "--no-verify", "-m", "old"], check=True)
    stage(repo, "b.md", "plain text\n")
    assert tag_check.check("git commit -m y", str(repo)) == []


def test_a_non_commit_command_and_a_non_config_repo_pass(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "standards/ghost-topic\n")
    assert tag_check.check("git status", str(repo)) == []
    other = tmp_path / "other"
    other.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(other)], check=True)
    assert tag_check.check("git commit -m y", str(other)) == []
