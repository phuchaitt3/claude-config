"""PreToolUse hook: stop agents from merging a pull request that is the user's to merge or is red.

For a command that runs `gh pr merge` (or merges through `gh api`), it refuses:
- `--admin`, and any merge through `gh api`;
- any merge in a repository whose CLAUDE.md does not declare the solo-fast tier (read from the
  repository named by `--repo` when given, otherwise from the local checkout);
- a pull request touching a user-merge path;
- a pull request with a check that has not passed, or with no checks yet in a repository that has
  workflows;
- `--auto` when no check is required, because then nothing makes GitHub wait for CI (standard:
  standards/auto-merge-without-protection, checked 2026-11-05).

With `--auto` and required checks, GitHub holds the merge, so pending checks are allowed.
If gh cannot answer, or the hook itself fails, the merge is refused. A hook timeout still lets the
command through.

This is a guard against mistakes, not a security boundary: a merge in a form it does not parse gets
past it, and a push that adds a protected file after `--auto` is merged unseen (standard:
standards/agent-permission-enforcement, checked 2026-11-05).
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

# Paths the user merges (`workflow:pr-review`). `.claude/` is drawn by risk there, which needs a
# reading of the diff, so the hook refuses all of it and the user decides.
USER_MERGE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"^\.github/workflows/", "CI config (.github/workflows/)"),
    (r"^\.claude/", "agent settings and hooks (.claude/)"),
    (r"^infra/", "infra/"),
    (r"(^|/)Dockerfile[^/]*$", "deploy config (Dockerfile)"),
    (r"(^|/)(docker-)?compose[^/]*\.ya?ml$", "deploy config (compose)"),
    (r"(^|/)\.env(?!\.example$)(\..*)?$", "secrets (.env)"),
    (r"\.(pem|key)$", "secrets (key file)"),
    (r"(^|/)credentials[^/]*\.json$", "secrets (credentials)"),
)

_SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|&\n()`]")
# A merge through the API: the REST `.../pulls/N/merge` endpoint, or the GraphQL mutations.
# Words like `mergedAt` or `merged:>=` in a read-only query must not match.
_API_MERGE = re.compile(
    r"\bgh(\.exe)?\s+api\b.*(/merge\b|mergePullRequest|enablePullRequestAutoMerge)",
    re.I | re.S,
)
# What may come before `gh` in a command: wrappers, `VAR=value`, and a wrapper's number.
_WRAPPERS = {"env", "command", "sudo", "time", "nohup", "timeout"}
_ASSIGNMENT_OR_NUMBER = re.compile(r"[A-Za-z_]\w*=.*|\d+[smhd]?")
_SHELL_C_FLAGS = {"-c", "-lc", "-command"}
# `gh` flags before the subcommand that take a value (`gh -R o/r pr merge 9`).
_GH_GLOBAL_VALUE_FLAGS = {"-R", "--repo", "--hostname"}
# Flags of `gh pr merge` that take a value, so the value is not mistaken for the PR argument.
_VALUE_FLAGS = {
    "-b",
    "--body",
    "-F",
    "--body-file",
    "-t",
    "--subject",
    "-R",
    "--repo",
    "--match-head-commit",
    "-A",
    "--author-email",
}

_PASSED = {"pass", "skipping"}
_NO_CHECKS = re.compile(r"no (required )?checks reported", re.I)
_SOLO_FAST = re.compile(r"tier:\s*\**\s*solo-fast", re.I)


def _gh(args: Sequence[str], cwd: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["gh", *args], cwd=cwd or ".", capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"could not run gh: {exc}") from exc


class Gh:
    """What the gate asks GitHub. Each method raises RuntimeError when gh cannot say."""

    def __init__(self, cwd: str = ".") -> None:
        self.cwd = cwd

    def files(self, pr_args: Sequence[str]) -> list[str]:
        result = _gh(["pr", "diff", *pr_args, "--name-only"], self.cwd)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"gh exited with {result.returncode}")
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def checks(self, pr_args: Sequence[str], required: bool = False) -> list[dict[str, str]]:
        """The PR's checks. gh exits non-zero for pending, failing and absent checks alike."""
        flags = ["--required"] if required else []
        result = _gh(["pr", "checks", *pr_args, *flags, "--json", "name,bucket"], self.cwd)
        if result.stdout.lstrip().startswith("["):
            return json.loads(result.stdout)
        if _NO_CHECKS.search(result.stderr + result.stdout):
            return []
        raise RuntimeError(result.stderr.strip() or f"gh exited with {result.returncode}")

    def has_workflows(self, pr_args: Sequence[str]) -> bool:
        repo = list(pr_args[pr_args.index("--repo") :][:2]) if "--repo" in pr_args else []
        result = _gh(["workflow", "list", *repo, "--json", "id"], self.cwd)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"gh exited with {result.returncode}")
        return bool(json.loads(result.stdout))

    def may_merge(self, pr_args: Sequence[str]) -> bool:
        """True only in a repository whose CLAUDE.md declares the solo-fast tier."""
        return _SOLO_FAST.search(self._claude_md(pr_args)) is not None

    def _claude_md(self, pr_args: Sequence[str]) -> str:
        if "--repo" in pr_args:
            repo = pr_args[pr_args.index("--repo") + 1]
            result = _gh(
                ["api", f"repos/{repo}/contents/CLAUDE.md",
                 "-H", "Accept: application/vnd.github.raw"],
                self.cwd,
            )
            return result.stdout if result.returncode == 0 else ""
        try:
            top = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"], cwd=self.cwd or ".", capture_output=True,
                text=True, timeout=10, check=False,
            ).stdout.strip()
            return Path(top, "CLAUDE.md").read_text(encoding="utf-8") if top else ""
        except (OSError, subprocess.TimeoutExpired):
            return ""


def _is_gh(token: str) -> bool:
    name = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name in ("gh", "gh.exe")


def _gh_merge_args(tokens: Sequence[str]) -> list[str] | None:
    """Arguments after `gh [global flags] pr merge`, or None if `tokens` is not that."""
    i = 0
    while i < len(tokens) and (tokens[i] in _WRAPPERS or _ASSIGNMENT_OR_NUMBER.fullmatch(tokens[i])):
        i += 1
    if i >= len(tokens) or not _is_gh(tokens[i]):
        return None
    j = i + 1
    while j < len(tokens) and tokens[j].startswith("-"):
        j += 2 if tokens[j] in _GH_GLOBAL_VALUE_FLAGS else 1
    return list(tokens[j + 2 :]) if tokens[j : j + 2] == ["pr", "merge"] else None


def _merge_segments(command: str) -> list[list[str]]:
    """Token lists for each `gh pr merge ...` in a shell command.

    Looks through chains (`&&`, `;`, `|`), `$(...)`, backticks and a shell's `-c` argument, and
    matches `gh` only where a command starts, so a commit message that names it is not a merge.
    """
    found: list[list[str]] = []
    for segment in _SEGMENT_SPLIT.split(command.replace("$(", ";")):
        text = segment.replace("\\", "/")  # shlex would drop the backslashes of a Windows path
        try:
            tokens = shlex.split(text, posix=True)
        except ValueError:
            tokens = text.split()
        args = _gh_merge_args(tokens)
        if args is not None:
            found.append(args)
        for flag, token in zip(tokens, tokens[1:], strict=False):
            if flag.lower() in _SHELL_C_FLAGS and "merge" in token:
                found.extend(_merge_segments(token))
    return found


def _pr_args(merge_args: Sequence[str]) -> list[str]:
    """The PR selector and --repo, if any, to pass on to `gh pr diff`."""
    selector: list[str] = []
    repo: list[str] = []
    skip = False
    for i, arg in enumerate(merge_args):
        if skip:
            skip = False
            continue
        if arg in ("-R", "--repo") and i + 1 < len(merge_args):
            repo = ["--repo", merge_args[i + 1]]
            skip = True
        elif arg.startswith("--repo="):
            repo = ["--repo", arg.split("=", 1)[1]]
        elif arg in _VALUE_FLAGS:
            skip = True
        elif not arg.startswith("-") and not selector:
            selector = [arg]
    return [*selector, *repo]


def user_merge_hits(files: Sequence[str]) -> list[tuple[str, str]]:
    """(file, reason) for every changed file on the user-merge list."""
    hits: list[tuple[str, str]] = []
    for name in files:
        normalized = name.replace("\\", "/")
        for pattern, reason in USER_MERGE_PATTERNS:
            if re.search(pattern, normalized, flags=re.IGNORECASE):
                hits.append((name, reason))
                break
    return hits


def ci_refusal(merge_args: Sequence[str], pr_args: Sequence[str], gh: Gh) -> str | None:
    """Why CI blocks this merge, or None."""
    if "--auto" in merge_args:
        if gh.checks(pr_args, required=True):
            return None  # GitHub holds the merge until the required checks pass
        return (
            "`--auto` is not a gate here: this repository has no required checks, so nothing "
            "makes GitHub wait for CI. Run `gh pr checks <n> --watch`, then merge without `--auto`."
        )
    checks = gh.checks(pr_args)
    if not checks:
        if gh.has_workflows(pr_args):
            return "CI has not reported on this PR yet. Run `gh pr checks <n> --watch` first."
        return None
    bad = [f"{c.get('name')}: {c.get('bucket')}" for c in checks if c.get("bucket") not in _PASSED]
    if bad:
        return "These checks have not passed, so the merge is refused:\n  - " + "\n  - ".join(bad)
    return None


def check(command: str, gh: Gh) -> str | None:
    """Return a refusal reason for `command`, or None when it may run."""
    if _API_MERGE.search(command):
        return (
            "Merging through `gh api` skips the merge gate. "
            "Use `gh pr merge`, and only on PRs that are not the user's to merge."
        )
    for merge_args in _merge_segments(command):
        if "--disable-auto" in merge_args:
            continue
        if any(a == "--admin" or a.startswith("--admin=") for a in merge_args):
            return "`gh pr merge --admin` bypasses repository rules and is never allowed for agents."
        pr_args = _pr_args(merge_args)
        try:
            if not gh.may_merge(pr_args):
                return (
                    "Agents may merge only in a project that declares the solo-fast tier in its "
                    "CLAUDE.md. Here the user merges: label the PR `needs-you` and request their "
                    "review."
                )
            hits = user_merge_hits(gh.files(pr_args))
            if hits:
                lines = "\n".join(f"  - {name}: {reason}" for name, reason in hits)
                return (
                    f"This PR touches paths the user merges:\n{lines}\n"
                    "Label it `needs-you` and request the user's review instead of merging."
                )
            reason = ci_refusal(merge_args, pr_args, gh)
        except (RuntimeError, ValueError, IndexError) as exc:
            return f"GitHub could not confirm this merge is safe, so it is refused: {exc}"
        if reason:
            return reason
    return None


def _deny(reason: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") not in ("Bash", "PowerShell"):
        return 0
    tool_input = payload.get("tool_input")
    command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
    if "merge" not in command.lower():
        return 0
    try:
        reason = check(command, Gh(str(payload.get("cwd") or ".")))
    except Exception as exc:  # fail closed: an exit code other than 0 or 2 would let it through
        reason = f"The merge gate failed ({type(exc).__name__}: {exc}), so the merge is refused."
    if reason is not None:
        _deny(reason)
    return 0


if __name__ == "__main__":
    sys.exit(main())
