import importlib.util
import io
import json
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "github_state", Path(__file__).with_name("github_state.py")
)
assert _spec and _spec.loader
github_state = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(github_state)


def state(open_prs=(), merged=(), branch=()):
    return {
        "open": [
            {"number": n, "title": t, "labels": [{"name": x} for x in labels], "isDraft": False}
            for n, t, labels in open_prs
        ],
        "merged": [{"number": n, "mergedAt": f"2026-10-30T{h:02d}:00:00Z"} for n, h in merged],
        "branch": [{"number": n, "state": s} for n, s in branch],
    }


def test_describe_lists_open_needs_you_and_merged() -> None:
    line, merged, warning = github_state.describe(
        state(open_prs=[(32, "docs", ["needs-you"]), (33, "x", [])], merged=[(28, 11), (27, 10)]),
        None,
    )
    assert "#32 docs" in line and "needs-you PRs: #32" in line
    assert "#28 (11:00Z), #27 (10:00Z)" in line
    assert merged == [28, 27] and warning == ""


def test_branch_of_a_merged_pr_gets_a_warning() -> None:
    _, _, warning = github_state.describe(state(branch=[(27, "MERGED")]), "fix/T11-followups")
    assert "#27" in warning and "do not push" in warning


def test_branch_with_an_open_pr_or_none_gets_no_warning() -> None:
    assert github_state.describe(state(branch=[(30, "OPEN")]), "b")[2] == ""
    assert github_state.describe(state(branch=[(5, "MERGED"), (6, "OPEN")]), "b")[2] == ""
    assert github_state.describe(state(branch=[]), "b")[2] == ""


def run_main(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path,
             fake_state: dict, branch: str | None = "feat/x") -> str:
    monkeypatch.setattr(github_state, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(github_state, "github_repo", lambda _cwd: "o/r")
    monkeypatch.setattr(github_state, "current_branch", lambda _cwd: branch)
    monkeypatch.setattr(github_state, "read_state", lambda *_a: fake_state)
    monkeypatch.setattr("sys.stdin", io.StringIO('{"session_id":"s1","cwd":"."}'))
    github_state.main()
    return capsys.readouterr().out


def test_first_message_reports_then_quiet_until_something_changes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    first = run_main(monkeypatch, capsys, tmp_path, state(open_prs=[(32, "docs", [])]))
    assert "open PRs: #32 docs" in json.loads(first)["hookSpecificOutput"]["additionalContext"]
    assert run_main(monkeypatch, capsys, tmp_path, state(open_prs=[(32, "docs", [])])) == ""


def test_a_new_merge_adds_the_after_a_merge_steps(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    run_main(monkeypatch, capsys, tmp_path, state(open_prs=[(32, "docs", [])]))
    out = run_main(monkeypatch, capsys, tmp_path, state(merged=[(32, 12)]))
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "New merges since your last check: #32" in context
    assert "no force-push" in context


def test_first_report_does_not_claim_new_merges(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    out = run_main(monkeypatch, capsys, tmp_path, state(merged=[(28, 11)]))
    assert "New merges" not in json.loads(out)["hookSpecificOutput"]["additionalContext"]


def test_outside_a_github_repo_it_prints_nothing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    monkeypatch.setattr(github_state, "github_repo", lambda _cwd: None)
    monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
    github_state.main()
    assert capsys.readouterr().out == ""
