import importlib.util
from collections.abc import Sequence
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "merge_gate", Path(__file__).with_name("merge_gate.py")
)
assert _spec and _spec.loader
merge_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(merge_gate)


def files(*names: str):
    def fn(_args: Sequence[str]) -> list[str]:
        return list(names)

    return fn


def test_claude_md_is_refused_with_file_name() -> None:
    reason = merge_gate.check("gh pr merge 9 --auto --squash", files("CLAUDE.md", "README.md"))
    assert reason and "CLAUDE.md" in reason


def test_api_only_pr_passes() -> None:
    assert (
        merge_gate.check(
            "gh pr merge 7 --squash", files("apps/api/src/x.py", "apps/api/tests/t.py")
        )
        is None
    )


@pytest.mark.parametrize(
    "command",
    [
        "gh pr merge 7 --admin --squash",
        "gh pr merge --admin 7",
        "cd x && gh pr merge 7 --squash --admin",
    ],
)
def test_admin_always_refused(command: str) -> None:
    reason = merge_gate.check(command, files("apps/api/src/x.py"))
    assert reason and "--admin" in reason


@pytest.mark.parametrize(
    "path",
    [
        "infra/main.tf",
        ".github/workflows/ci.yml",
        ".github/CODEOWNERS",
        "apps/api/Dockerfile",
        "docker-compose.yml",
        "compose.yaml",
        ".env",
        "certs/server.pem",
        "apps/api/src/book_rag_api/auth/session.py",
        ".claude/hooks/merge_gate.py",
    ],
)
def test_user_merge_paths_refused(path: str) -> None:
    assert merge_gate.check("gh pr merge 5 --squash", files("apps/api/x.py", path))


@pytest.mark.parametrize(
    "path",
    [
        "apps/api/src/book_rag_api/author.py",
        "packages/rag/src/x.py",
        "apps/web/README.md",
        "README.md",  # the project copy of the hook guards public positioning; the floor does not
        ".env.example",
        "uv.lock",
        "apps/web/pnpm-lock.yaml",
    ],
)
def test_ordinary_paths_pass(path: str) -> None:
    assert merge_gate.check("gh pr merge 5 --squash", files(path)) is None


def test_chained_command_is_still_checked() -> None:
    assert merge_gate.check("cd repo && gh pr merge 9 --squash", files("CLAUDE.md"))


def test_non_merge_commands_pass_without_calling_gh() -> None:
    def boom(_args: Sequence[str]) -> list[str]:
        raise AssertionError("gh must not be called")

    assert merge_gate.check("gh pr create --title x", boom) is None
    assert merge_gate.check("gh pr view 9", boom) is None


def test_gh_failure_fails_closed() -> None:
    def fail(_args: Sequence[str]) -> list[str]:
        raise RuntimeError("no network")

    reason = merge_gate.check("gh pr merge 9 --squash", fail)
    assert reason and "refused" in reason


def test_gh_api_merge_refused() -> None:
    assert merge_gate.check("gh api -X PUT repos/o/r/pulls/9/merge", files("a.py"))


def test_pr_selector_and_repo_are_passed_on() -> None:
    seen: list[list[str]] = []

    def fn(args: Sequence[str]) -> list[str]:
        seen.append(list(args))
        return []

    merge_gate.check("gh pr merge --squash -b 'note' --repo o/r 12", fn)
    assert seen == [["12", "--repo", "o/r"]]


@pytest.mark.parametrize(
    "command",
    [
        "bash -c 'gh pr merge 9 --squash'",
        'sh -c "gh pr merge 9 --squash"',
        "gh -R o/r pr merge 9",
        "gh --repo o/r pr merge 9 --auto",
        "echo $(gh pr merge 9)",
        "echo `gh pr merge 9`",
        "gh.exe pr merge 9",
        "/usr/bin/gh pr merge 9",
        "true & gh pr merge 9",
        "(gh pr merge 9)",
    ],
)
def test_wrapped_merge_forms_are_checked(command: str) -> None:
    assert merge_gate.check(command, files("CLAUDE.md"))


@pytest.mark.parametrize(
    "command",
    [
        "gh api graphql -f query='mutation{mergePullRequest(input:{})}'",
        "gh api graphql -f query='mutation{enablePullRequestAutoMerge(input:{})}'",
        "gh api -X PUT repos/o/r/pulls/9/merge",
    ],
)
def test_gh_api_merge_forms_refused(command: str) -> None:
    assert merge_gate.check(command, files("a.py"))


def test_repo_flag_before_subcommand_is_skipped() -> None:
    seen: list[list[str]] = []

    def fn(args: Sequence[str]) -> list[str]:
        seen.append(list(args))
        return []

    merge_gate.check("gh -R o/r pr merge 12 --squash", fn)
    assert seen == [["12"]]


def _run_main(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], payload: str
) -> tuple[int, str]:
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    code = merge_gate.main()
    return code, capsys.readouterr().out


def test_main_denies_when_the_gate_itself_crashes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def boom(_command: str, **_kwargs: object) -> str | None:
        raise ValueError("bug")

    monkeypatch.setattr(merge_gate, "check", boom)
    payload = '{"tool_name":"Bash","tool_input":{"command":"gh pr merge 9"}}'
    code, out = _run_main(monkeypatch, capsys, payload)
    assert code == 0 and '"deny"' in out


def test_main_ignores_other_commands_and_odd_payloads(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for payload in (
        '{"tool_name":"Bash","tool_input":{"command":"git status"}}',
        '{"tool_name":"Bash","tool_input":"oops"}',
        "[]",
    ):
        assert _run_main(monkeypatch, capsys, payload) == (0, "")


def test_read_only_gh_api_queries_with_merge_words_pass() -> None:
    for command in (
        "gh api repos/o/r/issues/27/timeline --jq '.[] | select(.event==\"merged\")'",
        "gh search prs --search 'merged:>=2026-10-30' --json mergedAt",
        "gh api repos/o/r/pulls/9 --jq .merged_at",
    ):
        assert merge_gate.check(command, files("a.py")) is None


def test_outside_a_solo_fast_project_every_merge_is_refused() -> None:
    reason = merge_gate.check("gh pr merge 5 --squash", files("docs/x.md"), may_merge=False)
    assert reason and "solo-fast" in reason


def test_agents_may_merge_reads_the_tier_from_claude_md(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    assert merge_gate.agents_may_merge(str(tmp_path)) is False  # no CLAUDE.md
    (tmp_path / "CLAUDE.md").write_text("# p\n\nTier: **standard**\n", encoding="utf-8")
    assert merge_gate.agents_may_merge(str(tmp_path)) is False
    (tmp_path / "CLAUDE.md").write_text("# p\n\nTier: **solo-fast** (ok)\n", encoding="utf-8")
    assert merge_gate.agents_may_merge(str(tmp_path)) is True


def test_powershell_tool_is_gated_too(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(merge_gate, "agents_may_merge", lambda _cwd: False)
    payload = '{"tool_name":"PowerShell","cwd":".","tool_input":{"command":"gh pr merge 9"}}'
    code, out = _run_main(monkeypatch, capsys, payload)
    assert code == 0 and '"deny"' in out
