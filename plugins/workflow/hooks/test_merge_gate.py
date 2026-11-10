import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("merge_gate", Path(__file__).with_name("merge_gate.py"))
assert _spec and _spec.loader
merge_gate = importlib.util.module_from_spec(_spec)
sys.modules["merge_gate"] = merge_gate
_spec.loader.exec_module(merge_gate)

GREEN = [{"name": "core", "bucket": "pass"}]


class FakeGh:
    def __init__(self, *, solo=True, files=("src/a.py",), checks=GREEN, required=(), workflows=True,
                 error=None):
        self.solo, self.file_list, self.all_checks = solo, list(files), list(checks)
        self.required, self.workflows, self.error = list(required), workflows, error
        self.seen: list[list[str]] = []

    def _fail(self):
        if self.error:
            raise RuntimeError(self.error)

    def may_merge(self, pr_args):
        self.seen.append(list(pr_args))
        return self.solo

    def files(self, pr_args):
        self._fail()
        return self.file_list

    def checks(self, pr_args, required=False):
        self._fail()
        return self.required if required else self.all_checks

    def required_checks(self, pr_args):
        self._fail()
        return [c["name"] for c in self.required]

    def has_workflows(self, pr_args):
        return self.workflows


def test_green_pr_in_a_solo_fast_repo_merges() -> None:
    assert merge_gate.check("gh pr merge 4 --squash --delete-branch", FakeGh()) is None


@pytest.mark.parametrize("bucket", ["fail", "pending", "cancel"])
def test_a_check_that_has_not_passed_blocks_the_merge(bucket: str) -> None:
    gh = FakeGh(checks=[*GREEN, {"name": "lint", "bucket": bucket}])
    reason = merge_gate.check("gh pr merge 4 --squash", gh)
    assert reason and f"lint: {bucket}" in reason


def test_a_skipped_check_does_not_block() -> None:
    gh = FakeGh(checks=[*GREEN, {"name": "docs", "bucket": "skipping"}])
    assert merge_gate.check("gh pr merge 4 --squash", gh) is None


def test_no_checks_yet_blocks_a_repo_with_workflows() -> None:
    reason = merge_gate.check("gh pr merge 4 --squash", FakeGh(checks=[]))
    assert reason and "not reported" in reason


def test_no_checks_is_fine_in_a_repo_without_workflows() -> None:
    assert merge_gate.check("gh pr merge 4 --squash", FakeGh(checks=[], workflows=False)) is None


def test_auto_without_required_checks_is_refused_even_when_green() -> None:
    reason = merge_gate.check("gh pr merge 4 --auto --squash", FakeGh())
    assert reason and "not a gate" in reason


def test_auto_with_required_checks_may_wait_on_pending_checks() -> None:
    gh = FakeGh(checks=[{"name": "core", "bucket": "pending"}], required=GREEN)
    assert merge_gate.check("gh pr merge 4 --auto --squash", gh) is None


def test_disable_auto_is_not_a_merge() -> None:
    assert merge_gate.check("gh pr merge 4 --disable-auto", FakeGh(solo=False)) is None


@pytest.mark.parametrize(
    "path",
    [".github/workflows/ci.yml", ".claude/settings.json", "infra/main.tf", "app/Dockerfile",
     "docker-compose.dev.yml", ".env", "conf/.env.prod", "certs/server.pem", "credentials.json"],
)
def test_user_merge_paths_are_refused(path: str) -> None:
    reason = merge_gate.check("gh pr merge 4 --squash", FakeGh(files=[path]))
    assert reason and path in reason and "needs-you" in reason


@pytest.mark.parametrize(
    "path",
    ["CLAUDE.md", "README.md", ".github/CODEOWNERS", ".env.example", "src/permissions.py",
     "uv.lock"],
)
def test_ordinary_paths_merge(path: str) -> None:
    assert merge_gate.check("gh pr merge 4 --squash", FakeGh(files=[path])) is None


def test_outside_a_solo_fast_repo_every_merge_is_refused() -> None:
    reason = merge_gate.check("gh pr merge 4 --squash", FakeGh(solo=False))
    assert reason and "solo-fast" in reason


def test_admin_is_refused_before_anything_else() -> None:
    reason = merge_gate.check("gh pr merge 4 --admin --squash", FakeGh())
    assert reason and "--admin" in reason


@pytest.mark.parametrize(
    "command",
    ["gh api repos/o/r/pulls/4/merge -X PUT", "gh api graphql -f query='mutation{mergePullRequest}'"],
)
def test_merging_through_the_api_is_refused(command: str) -> None:
    assert merge_gate.check(command, FakeGh())


def test_read_only_api_call_mentioning_merged_is_allowed() -> None:
    assert merge_gate.check("gh api repos/o/r/pulls --jq '.[].merged_at'", FakeGh()) is None


@pytest.mark.parametrize(
    "command",
    ["cd x && gh pr merge 4 --squash", "git fetch; gh pr merge 4", "bash -c 'gh pr merge 4'",
     "gh -R o/r pr merge 4", "gh.exe pr merge 4", r"C:\tools\gh.exe pr merge 4",
     "GH_TOKEN=x gh pr merge 4", "timeout 60 gh pr merge 4", "pwsh -Command 'gh pr merge 4'"],
)
def test_merges_are_found_in_any_command_form(command: str) -> None:
    assert merge_gate.check(command, FakeGh(checks=[{"name": "c", "bucket": "fail"}]))


def test_the_repo_flag_reaches_the_tier_lookup() -> None:
    gh = FakeGh()
    merge_gate.check("gh pr merge 4 --repo o/r --squash", gh)
    assert gh.seen == [["4", "--repo", "o/r"]]


def test_gh_failure_refuses_the_merge() -> None:
    reason = merge_gate.check("gh pr merge 4 --squash", FakeGh(error="network down"))
    assert reason and "network down" in reason


@pytest.mark.parametrize(
    "command",
    ["gh pr list", "gh pr view 4", "git merge main", "echo gh pr merge is a command",
     'git commit -m "Use gh pr merge without --auto"', "grep -n 'gh pr merge' SKILL.md"],
)
def test_other_commands_pass(command: str) -> None:
    assert merge_gate.check(command, FakeGh(solo=False)) is None


class _Result:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout, self.stderr, self.returncode = stdout, stderr, returncode


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (_Result('[{"name":"core","bucket":"fail"}]', "", 1), [{"name": "core", "bucket": "fail"}]),
        (_Result('[{"name":"core","bucket":"pending"}]', "", 8),
         [{"name": "core", "bucket": "pending"}]),
        (_Result("", "no required checks reported on the 'x' branch", 1), []),
        (_Result("", "no checks reported on the 'x' branch", 1), []),
    ],
)
def test_checks_reads_gh_whatever_its_exit_code(monkeypatch, result, expected) -> None:
    monkeypatch.setattr(merge_gate, "_gh", lambda args, cwd: result)
    assert merge_gate.Gh().checks(["4"]) == expected


def test_auto_is_allowed_before_ci_reports_when_the_branch_requires_checks() -> None:
    # 2026-11-10: right after a push no check had reported, and the gate wrongly said the
    # repository required none, though its ruleset required three.
    gh = FakeGh(checks=[], required=GREEN)
    assert merge_gate.check("gh pr merge 4 --auto --squash", gh) is None


def _api(responses: dict):
    """A fake _gh answering `pr view` and `api <path>` calls from `responses`."""

    def fake(args, cwd):
        if args[:2] == ["pr", "view"]:
            return _Result('{"baseRefName":"main","url":"https://github.com/o/r/pull/4"}')
        return responses[args[1]]

    return fake


RULES = "repos/o/r/rules/branches/main"
BRANCH = "repos/o/r/branches/main"
RULESET = ('[{"type":"pull_request"},{"type":"required_status_checks","parameters":'
           '{"required_status_checks":[{"context":"web"},{"context":"python"}]}}]')
CLASSIC = '{"protected":true,"protection":{"required_status_checks":{"contexts":["lint"]}}}'


@pytest.mark.parametrize(
    ("rules", "branch", "expected"),
    [
        (RULESET, '{"protected":true,"protection":{}}', ["python", "web"]),
        ("[]", CLASSIC, ["lint"]),
        (RULESET, CLASSIC, ["lint", "python", "web"]),
        ("[]", '{"protected":false}', []),
    ],
)
def test_required_checks_reads_rulesets_and_classic_protection(
    monkeypatch, rules, branch, expected
) -> None:
    monkeypatch.setattr(merge_gate, "_gh", _api({RULES: _Result(rules), BRANCH: _Result(branch)}))
    assert merge_gate.Gh().required_checks(["4"]) == expected


def test_required_checks_raises_when_the_rules_cannot_be_read(monkeypatch) -> None:
    responses = {RULES: _Result("", "HTTP 404: Not Found", 1), BRANCH: _Result("{}")}
    monkeypatch.setattr(merge_gate, "_gh", _api(responses))
    with pytest.raises(RuntimeError, match="404"):
        merge_gate.Gh().required_checks(["4"])


def test_checks_raises_on_a_real_gh_error(monkeypatch) -> None:
    monkeypatch.setattr(merge_gate, "_gh", lambda a, c: _Result("", "Could not resolve", 1))
    with pytest.raises(RuntimeError, match="Could not resolve"):
        merge_gate.Gh().checks(["4"])


@pytest.mark.parametrize(
    ("text", "expected"),
    [("**Tier: solo-fast. Mode: build.**", True), ("Tier: **solo-fast**", True),
     ("Tier: standard", False), ("", False)],
)
def test_the_tier_is_read_from_the_named_repo(monkeypatch, text: str, expected: bool) -> None:
    calls: list = []

    def fake(args, cwd):
        calls.append(args)
        return _Result(text)

    monkeypatch.setattr(merge_gate, "_gh", fake)
    assert merge_gate.Gh().may_merge(["4", "--repo", "o/r"]) is expected
    assert calls[0][1] == "repos/o/r/contents/CLAUDE.md"


def run_main(monkeypatch, capsys, payload: dict) -> str:
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert merge_gate.main() == 0
    return capsys.readouterr().out


def test_main_denies_with_the_hook_format(monkeypatch, capsys) -> None:
    monkeypatch.setattr(merge_gate, "Gh", lambda cwd: FakeGh(solo=False))
    out = run_main(monkeypatch, capsys, {"tool_name": "Bash",
                                         "tool_input": {"command": "gh pr merge 4"}, "cwd": "."})
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_main_fails_closed_on_a_bug(monkeypatch, capsys) -> None:
    def broken(command, gh):
        raise KeyError("bug")

    monkeypatch.setattr(merge_gate, "check", broken)
    out = run_main(monkeypatch, capsys, {"tool_name": "Bash",
                                         "tool_input": {"command": "gh pr merge 4"}, "cwd": "."})
    assert "failed" in json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]


def test_main_ignores_other_tools(monkeypatch, capsys) -> None:
    out = run_main(monkeypatch, capsys, {"tool_name": "Read", "tool_input": {"file_path": "merge"}})
    assert out == ""
