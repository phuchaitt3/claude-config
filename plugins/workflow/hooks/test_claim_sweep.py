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


def decide(comments, prs=(), live=frozenset(), number=7):
    return claim_sweep.decide(number, comments, list(prs), set(live), HOST, NOW)


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
