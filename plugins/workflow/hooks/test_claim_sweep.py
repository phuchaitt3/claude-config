import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "claim_sweep", Path(__file__).with_name("claim_sweep.py")
)
assert _spec and _spec.loader
claim_sweep = importlib.util.module_from_spec(_spec)
sys.modules["claim_sweep"] = claim_sweep
_spec.loader.exec_module(claim_sweep)

NOW = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
HOST = "BOX"


def at(hours_ago: float) -> str:
    return (NOW - timedelta(hours=hours_ago)).isoformat().replace("+00:00", "Z")


def claim(hours_ago: float, body: str = "claimed by 7999fa (uuid 544bc8ec, BOX). Files: a.py"):
    return {"createdAt": at(hours_ago), "body": body}


def decide(comments, prs=(), live=frozenset(), number=7, idle=frozenset()):
    return claim_sweep.decide(number, comments, list(prs), set(live), HOST, NOW, set(idle))


def test_gone_session_is_released() -> None:
    release, _, prefix = decide([claim(3)])
    assert release and prefix == "544bc8ec"


def test_running_session_is_kept() -> None:
    assert not decide([claim(3)], live={"544bc8ec"})[0]


def test_young_claim_is_kept() -> None:
    assert not decide([claim(1)])[0]


def test_open_pr_by_number_or_branch_keeps_the_claim() -> None:
    assert not decide([claim(3)], prs=[{"title": "x", "body": "Closes #7", "headRefName": "a"}])[0]
    assert not decide([claim(3)], prs=[{"title": "x", "body": "", "headRefName": "fix/7-slug"}])[0]
    assert decide([claim(3)], prs=[{"title": "x", "body": "Closes #77", "headRefName": "fix/77-a"}])[0]


def test_other_machine_is_never_released() -> None:
    other = claim(99, "claimed by abc123 (uuid 11112222, OTHER). Files: a")
    assert not decide([other])[0]


def test_claim_without_uuid_waits_a_day() -> None:
    assert not decide([claim(23, "claimed by 26d91d. Files: a")])[0]
    assert decide([claim(25, "claimed by 26d91d. Files: a")])[0]


def test_latest_claim_wins() -> None:
    old = claim(50)
    new = claim(1, "claimed by 111111 (uuid aaaaaaaa, BOX). Files: b")
    assert not decide([old, new])[0]


def test_label_without_claim_comment_is_kept() -> None:
    assert not decide([{"createdAt": at(9), "body": "just a comment"}])[0]


def test_live_prefixes_reads_session_files(tmp_path: Path) -> None:
    alive = {"pid": os.getpid(), "sessionId": "ABCDEF12-0000"}
    dead = {"pid": 2**22 - 3, "sessionId": "deadbeef-0000"}
    (tmp_path / "1.json").write_text(json.dumps(alive))
    (tmp_path / "2.json").write_text(json.dumps(dead))
    (tmp_path / "3.json").write_text("not json")
    assert claim_sweep.live_prefixes(tmp_path) == {"abcdef12"}


def _draft(hours_since_commit: float, draft: bool = True) -> dict:
    return {"title": "x", "body": "Closes #7", "headRefName": "a", "isDraft": draft,
            "commits": [{"committedDate": at(hours_since_commit)}]}


def test_draft_pr_quiet_over_six_hours_no_longer_holds_the_claim() -> None:
    assert decide([claim(30)], prs=[_draft(7)])[0]
    assert not decide([claim(30)], prs=[_draft(5)])[0]
    assert not decide([claim(30)], prs=[_draft(30, draft=False)])[0]  # a ready PR keeps it
    assert not decide([claim(30)], prs=[{"title": "x", "body": "#7", "headRefName": "a", "isDraft": True}])[0]


def test_running_session_idle_over_six_hours_no_longer_holds_the_claim() -> None:
    assert decide([claim(30)], live={"544bc8ec"}, idle={"544bc8ec"})[0]
    assert not decide([claim(30)], live={"544bc8ec"})[0]


def test_idle_prefixes_reads_transcript_age(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    proj.mkdir()
    old, fresh = proj / "aaaaaaaa-1.jsonl", proj / "bbbbbbbb-2.jsonl"
    for f, hours in ((old, 8), (fresh, 1)):
        f.write_text("{}")
        t = (NOW - timedelta(hours=hours)).timestamp()
        os.utime(f, (t, t))
    got = claim_sweep.idle_prefixes({"aaaaaaaa", "bbbbbbbb", "cccccccc"}, NOW, tmp_path)
    assert got == {"aaaaaaaa"}


def test_sweep_passes_the_repo_to_gh(monkeypatch, tmp_path) -> None:
    calls = []

    def fake(main, *args, repo=None):
        calls.append((args[0], repo))
        return []

    monkeypatch.setattr(claim_sweep, "gh_json", fake)
    assert claim_sweep.sweep(tmp_path, dry_run=True, repo="o/r") == []
    assert calls == [("issue", "o/r")]
