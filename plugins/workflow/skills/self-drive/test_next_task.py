import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("next_task", Path(__file__).with_name("next_task.py"))
assert _spec and _spec.loader
next_task = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(next_task)


def issue(n, labels=(), blocked_by=(), blocking=(), body="", created="2026-10-30"):
    return {
        "number": n,
        "title": f"t{n}",
        "body": body,
        "createdAt": f"{created}T00:00:00Z",
        "labels": {"nodes": [{"name": x} for x in labels]},
        "blockedBy": {"nodes": [{"number": m, "state": "OPEN"} for m in blocked_by]},
        "blocking": {"nodes": [{"number": m, "state": "OPEN"} for m in blocking]},
    }


def numbers(ranked):
    return [r["number"] for r in ranked]


def test_bottleneck_beats_priority_next_and_blocked_issues_are_left_out() -> None:
    issues = [
        issue(1, ["priority:next"], created="2026-10-01"),
        issue(2, ["priority:later"], blocking=[3, 4]),
        issue(3, ["priority:next"], blocked_by=[2]),
        issue(4, ["priority:now"], blocked_by=[2]),
    ]
    ranked, fixups = next_task.rank(issues)
    assert numbers(ranked) == [2, 1]
    assert ranked[0]["tier"] == 0 and ranked[0]["blocks"] == 2
    assert any("#2: blocks 2" in f for f in fixups)


def test_transitive_blocking_counts() -> None:
    issues = [
        issue(1, ["priority:next"], blocking=[2]),
        issue(2, blocked_by=[1], blocking=[3]),
        issue(3, blocked_by=[2]),
        issue(4, ["priority:next"], blocking=[5], created="2026-10-01"),
        issue(5, blocked_by=[4]),
    ]
    ranked, _ = next_task.rank(issues)
    assert numbers(ranked) == [1, 4]  # 1 blocks two issues through 2, so it is a bottleneck
    assert ranked[0]["blocks"] == 2


def test_closed_blocker_does_not_block() -> None:
    i = issue(1, ["priority:next"])
    i["blockedBy"]["nodes"] = [{"number": 9, "state": "CLOSED"}]
    ranked, _ = next_task.rank([i])
    assert numbers(ranked) == [1]


def test_claimed_and_needs_you_are_skipped() -> None:
    ranked, _ = next_task.rank([issue(1, ["claimed"]), issue(2, ["needs-you"]), issue(3)])
    assert numbers(ranked) == [3]


def test_text_dependency_without_link_is_a_fixup() -> None:
    issues = [issue(1, body="Blocked by #2 and blocked by #99"), issue(2)]
    _, fixups = next_task.rank(issues)
    assert fixups == ["#1: body says 'Blocked by #2' but has no dependency link; add it"]


def test_cycle_does_not_loop() -> None:
    issues = [issue(1, blocking=[2], blocked_by=[2]), issue(2, blocking=[1], blocked_by=[1])]
    ranked, _ = next_task.rank(issues)
    assert ranked == []


def test_render_says_how_many_issues_the_limit_cut() -> None:
    ranked, _ = next_task.rank([issue(n) for n in range(1, 5)])
    assert next_task.render(ranked, 2)[-1] == "... 2 more not shown (--limit)"
    assert len(next_task.render(ranked, 10)) == 4
    assert next_task.render([], 10) == ["no startable issue"]
