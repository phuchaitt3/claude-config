import importlib.util
import subprocess
from pathlib import Path

_spec = importlib.util.spec_from_file_location("tag_check", Path(__file__).with_name("tag_check.py"))
assert _spec and _spec.loader
tag_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tag_check)


def config_repo(path: Path) -> Path:
    (path / "plugins" / "workflow").mkdir(parents=True)
    (path / "findings").mkdir()
    (path / "findings" / "real-topic.md").write_text("x")
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
    return path


def stage(repo: Path, name: str, text: str) -> None:
    (repo / name).write_text(text)
    subprocess.run(["git", "-C", str(repo), "add", name], check=True)


def test_tag_to_an_existing_entry_passes(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "(standard: findings/real-topic, checked 2026-11-01)\n")
    assert tag_check.check("git commit -m y", str(repo)) == []


def test_tag_to_a_missing_entry_is_reported(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "(standard: findings/ghost-topic, checked 2026-11-01)\n")
    assert tag_check.check("git commit -m y", str(repo)) == ["ghost-topic"]


def test_the_old_standards_prefix_resolves_against_the_findings_folder(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "(standard: standards/real-topic, checked 2026-11-01)\n")
    assert tag_check.check("git commit -m y", str(repo)) == []
    stage(repo, "b.md", "(standard: standards/ghost-topic, checked 2026-11-01)\n")
    assert tag_check.check("git commit -m y", str(repo)) == ["ghost-topic"]


def test_a_url_with_standards_in_its_path_is_not_a_reference(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "[GDS](https://gds-way.example.uk/standards/architecture-decisions.html)\n")
    assert tag_check.check("git commit -m y", str(repo)) == []


def test_the_placeholder_in_the_template_is_ignored(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "one file per topic, `findings/<topic>.md`, tag findings/topic\n")
    assert tag_check.check("git commit -m y", str(repo)) == []


def test_only_added_lines_count(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "(standard: findings/ghost-topic, checked 2026-11-01)\n")
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-q", "--no-verify", "-m", "old"], check=True)
    stage(repo, "b.md", "plain text\n")
    assert tag_check.check("git commit -m y", str(repo)) == []


def test_a_non_commit_command_and_a_non_config_repo_pass(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    stage(repo, "a.md", "findings/ghost-topic\n")
    assert tag_check.check("git status", str(repo)) == []
    other = tmp_path / "other"
    other.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(other)], check=True)
    assert tag_check.check("git commit -m y", str(other)) == []



def unverified_entry(register: Path, topic: str, marked: bool) -> None:
    note = "> **Unverified (2026-11-15):** no Evidence strength field.\n" if marked else ""
    (register / f"{topic}.md").write_text(f"# T\n\n{note}- finding\n")


def test_a_tag_citing_an_unverified_entry_is_reported_in_the_config_repo(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    unverified_entry(repo / "findings", "old-topic", marked=True)
    unverified_entry(repo / "findings", "clean-topic", marked=False)
    stage(repo, "a.md", "(standard: findings/old-topic, checked 2026-11-01) (standard: findings/clean-topic)\n")
    assert tag_check.check_unverified("git commit -m y", str(repo)) == ["old-topic"]
    assert tag_check.check("git commit -m y", str(repo)) == []


def test_unverified_is_checked_in_other_repos_against_the_home_register(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home-register"
    home.mkdir()
    unverified_entry(home, "old-topic", marked=True)
    monkeypatch.setattr(tag_check, "HOME_REGISTER", home)
    other = tmp_path / "other"
    other.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(other)], check=True)
    stage(other, "a.tex", "% (standard: findings/old-topic, checked 2026-11-11)\n")
    assert tag_check.check_unverified("git commit -m y", str(other)) == ["old-topic"]
    assert tag_check.check("git commit -m y", str(other)) == []


def test_unverified_needs_a_standard_tag_and_a_commit_command(tmp_path: Path) -> None:
    repo = config_repo(tmp_path)
    unverified_entry(repo / "findings", "old-topic", marked=True)
    stage(repo, "a.md", "see findings/old-topic for the history\n")
    assert tag_check.check_unverified("git commit -m y", str(repo)) == []
    stage(repo, "b.md", "(standard: findings/old-topic)\n")
    assert tag_check.check_unverified("git status", str(repo)) == []


def test_main_warns_without_denying(tmp_path: Path, monkeypatch, capsys) -> None:
    import io
    import json

    repo = config_repo(tmp_path)
    unverified_entry(repo / "findings", "old-topic", marked=True)
    stage(repo, "a.md", "(standard: findings/old-topic, checked 2026-11-01)\n")
    payload = {"tool_name": "Bash", "tool_input": {"command": "git commit -m y"}, "cwd": str(repo)}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert tag_check.main() == 0
    out = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert "permissionDecision" not in out and "Unverified" in out["additionalContext"]
