import importlib.util
import io
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("push_guard", Path(__file__).with_name("push_guard.py"))
assert _spec and _spec.loader
push_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(push_guard)


def states(**by_branch: str):
    return lambda branch, _cwd: by_branch.get(branch, "none")


def test_push_of_a_merged_branch_is_refused() -> None:
    reason = push_guard.check("git push -u origin fix/T11", ".", states(**{"fix/T11": "merged"}))
    assert reason and "fix/T11" in reason and "new branch" in reason


@pytest.mark.parametrize(
    "command",
    [
        "git push origin fix/T11",
        "git push -u origin fix/T11",
        "git push origin HEAD:fix/T11",
        "git push origin +fix/T11",
        "git push origin refs/heads/fix/T11",
        "git -C ../wt push origin fix/T11",
        "cd x && git push --force-with-lease origin fix/T11",
    ],
)
def test_named_refspec_forms_are_checked(command: str) -> None:
    assert push_guard.check(command, ".", states(**{"fix/T11": "merged"}))


def test_cd_and_dash_c_change_the_folder_the_branch_is_read_from() -> None:
    import os

    base = os.path.normpath("/repo")
    assert push_guard.pushed_branches("cd .handoff && git push", "/repo") == [
        ("", os.path.join(base, ".handoff"))
    ]
    assert push_guard.pushed_branches("git -C .handoff push", "/repo") == [
        ("", os.path.join(base, ".handoff"))
    ]
    assert push_guard.pushed_branches("cd a && cd ../b && git push origin x", "/repo") == [
        ("x", os.path.join(base, "b"))
    ]


def test_push_after_cd_reads_the_current_branch_of_that_folder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import os

    asked: list[str] = []

    def fake_run(args: list[str], cwd: str) -> str:
        asked.append(cwd)
        return "main\n"  # the other folder is on the default branch: nothing to check

    monkeypatch.setattr(push_guard, "_run", fake_run)
    always_merged = lambda _b, _c: "merged"  # noqa: E731
    assert push_guard.check("cd .handoff && git push", "/repo", always_merged) is None
    assert asked == [os.path.join(os.path.normpath("/repo"), ".handoff")]


def test_bare_push_checks_the_current_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(push_guard, "_run", lambda args, cwd: "feat/x\n")
    assert push_guard.check("git push", ".", states(**{"feat/x": "merged"}))
    assert push_guard.check("git push origin HEAD", ".", states(**{"feat/x": "merged"}))


@pytest.mark.parametrize("state", ["open", "none"])
def test_open_or_missing_pr_is_allowed(state: str) -> None:
    assert push_guard.check("git push origin feat/x", ".", states(**{"feat/x": state})) is None


def test_default_branch_delete_and_tags_are_not_checked() -> None:
    always_merged = lambda _b, _c: "merged"  # noqa: E731
    assert push_guard.check("git push origin main", ".", always_merged) is None
    assert push_guard.check("git push origin --delete feat/x", ".", always_merged) is None
    assert push_guard.check("git push --tags", ".", always_merged) is None


def test_text_that_only_mentions_a_push_is_ignored() -> None:
    always_merged = lambda _b, _c: "merged"  # noqa: E731
    assert push_guard.check('git commit -m "then git push origin feat/x"', ".", always_merged) is None
    assert push_guard.check("echo git push origin feat/x", ".", always_merged) is None


def test_gh_failure_fails_open() -> None:
    def broken(_b: str, _c: str) -> str:
        raise RuntimeError("gh not logged in")

    assert push_guard.check("git push origin feat/x", ".", broken) is None


def test_main_denies_and_ignores_other_tools(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = '{"tool_name":"PowerShell","cwd":".","tool_input":{"command":"git push origin feat/x"}}'
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    monkeypatch.setattr(push_guard, "check", lambda _command, _cwd: "Branch `feat/x` is merged")
    assert push_guard.main() == 0
    assert '"deny"' in capsys.readouterr().out
    monkeypatch.setattr("sys.stdin", io.StringIO('{"tool_name":"Read","tool_input":{}}'))
    assert push_guard.main() == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    "command",
    [
        "git push --force origin fix/T11",
        "git push origin fix/T11 --force",
        "git push -f origin fix/T11",
        "git push -uf origin fix/T11",
        "git push --force-with-lease origin fix/T11",
        "git push --force-with-lease=fix/T11 origin fix/T11",
        "git push origin +fix/T11",
        "git push --mirror origin",
        "git -C ../wt push -f origin fix/T11",
        "cd x && git push -f",
    ],
)
def test_force_is_refused_even_where_main_may_be_pushed(command: str) -> None:
    reason = push_guard.policy_refusal(command, ".", lambda _d: True)
    assert reason and "Force" in reason


@pytest.mark.parametrize(
    "command",
    [
        "git push origin main",
        "git push -u origin main",
        "git push origin HEAD:main",
        "git push origin fix/T11:main",
        "git push origin refs/heads/main",
        "git push origin master",
        "git push origin :main",
        "git push origin --delete main",
        "git push --all origin",
    ],
)
def test_default_branch_is_refused_unless_the_repo_allows_it(command: str) -> None:
    reason = push_guard.policy_refusal(command, ".", lambda _d: False)
    assert reason and "default branch" in reason
    assert push_guard.policy_refusal(command, ".", lambda _d: True) is None


def _on_branch(monkeypatch, name: str) -> None:
    real = push_guard._run

    def fake(args, cwd):
        return name + "\n" if args[:2] == ["git", "branch"] else real(args, cwd)

    monkeypatch.setattr(push_guard, "_run", fake)


@pytest.mark.parametrize("command", ["git push", "git push origin", "git push origin HEAD"])
def test_a_bare_push_is_judged_by_the_current_branch(monkeypatch, command: str) -> None:
    _on_branch(monkeypatch, "main")
    assert push_guard.policy_refusal(command, ".", lambda _d: False)
    _on_branch(monkeypatch, "fix/T11")
    assert push_guard.policy_refusal(command, ".", lambda _d: False) is None


@pytest.mark.parametrize(
    "command",
    [
        "git push -u origin fix/T11",
        "git push origin fix/main-menu",
        "git push origin main:fix/T11",
        "git push --dry-run origin fix/T11",
        "git status",
        "echo git push -f",
    ],
)
def test_ordinary_commands_pass(command: str) -> None:
    assert push_guard.policy_refusal(command, ".", lambda _d: False) is None


def _repo_at(monkeypatch, top: Path) -> None:
    monkeypatch.setattr(push_guard, "_run", lambda args, cwd: str(top) + "\n")


@pytest.mark.parametrize(
    ("text", "expected"),
    [("**Tier: direct.**", True), ("Tier: **direct**", True), ("**Tier: solo-fast.**", False)],
)
def test_the_direct_tier_may_push_main(tmp_path, monkeypatch, text: str, expected: bool) -> None:
    (tmp_path / "CLAUDE.md").write_text(text, encoding="utf-8")
    _repo_at(monkeypatch, tmp_path)
    assert push_guard.may_push_default(".") is expected


def test_a_repo_with_no_claude_md_may_not_push_main(tmp_path, monkeypatch) -> None:
    _repo_at(monkeypatch, tmp_path)
    assert push_guard.may_push_default(".") is False


def test_the_config_repo_may_push_main(tmp_path, monkeypatch) -> None:
    (tmp_path / "claude-config").mkdir()
    monkeypatch.setattr(push_guard.Path, "home", lambda: tmp_path)
    _repo_at(monkeypatch, tmp_path / "claude-config")
    assert push_guard.may_push_default(".") is True


@pytest.mark.parametrize(("value", "expected"), [("allow\n", True), ("ALLOW\n", True), ("no\n", False), (None, False)])
def test_the_git_config_opt_in_may_push_main(tmp_path, monkeypatch, value, expected) -> None:
    def fake_run(args, cwd):
        if args[:2] == ["git", "config"]:
            if value is None:
                raise RuntimeError("key not set")
            return value
        return str(tmp_path) + "\n"

    monkeypatch.setattr(push_guard, "_run", fake_run)
    assert push_guard.may_push_default(".") is expected
