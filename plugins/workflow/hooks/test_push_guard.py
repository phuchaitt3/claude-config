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
