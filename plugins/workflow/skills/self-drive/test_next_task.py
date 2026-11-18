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


def test_resume_issues_beat_bottlenecks_and_priority_now() -> None:
    issues = [
        issue(1, ["priority:now"], created="2026-10-01"),
        issue(2, ["priority:later"], blocking=[3, 4]),
        issue(3, blocked_by=[2]),
        issue(4, blocked_by=[2]),
        issue(5, ["resume:3", "priority:later"]),
        issue(6, ["resume:1"], created="2026-11-01"),
    ]
    ranked, _ = next_task.rank(issues, ranks={})
    assert numbers(ranked) == [6, 5, 2, 1]  # then group 2: the bottleneck blocks more than #1


def test_blocker_of_a_resume_issue_inherits_its_kind_and_shorter_chain_wins() -> None:
    issues = [
        issue(1, blocking=[2]),
        issue(2, blocked_by=[1], blocking=[3]),
        issue(3, ["resume:2"], blocked_by=[2]),
        issue(4, blocking=[5], created="2026-11-01"),
        issue(5, ["resume:2"], blocked_by=[4]),
        issue(6, ["resume:1"], blocked_by=[7]),
        issue(7, ["priority:later"], blocking=[6], created="2026-11-02"),
    ]
    ranked, _ = next_task.rank(issues, ranks={})
    assert numbers(ranked) == [7, 4, 1]  # 7 unblocks resume:1; 4 reaches resume:2 in one step, 1 in two
    assert ranked[0]["resume"] == (1, next_task.NO_RANK, 1)
    assert next_task.render(ranked, 1)[0].startswith("#7\tresume:1 (unblocks, chain 1)")


def test_gap_rank_breaks_ties_within_a_resume_kind(tmp_path) -> None:
    gaps = tmp_path / "gaps.md"
    gaps.write_text("# x\n\n1. `llm-apps` LLM\n2. `agentic-ai` Agents\n", encoding="utf-8")
    ranks = next_task.gap_ranks(gaps)
    assert ranks == {"llm-apps": 0, "agentic-ai": 1}
    issues = [
        issue(1, ["resume:2", "gap:agentic-ai"], created="2026-10-01"),
        issue(2, ["resume:2", "gap:llm-apps"]),
        issue(3, ["resume:2"], created="2026-09-01"),
    ]
    ranked, _ = next_task.rank(issues, ranks=ranks)
    assert numbers(ranked) == [2, 1, 3]
    assert next_task.gap_ranks(tmp_path / "missing.md") == {}


def test_claimed_lists_only_claimed_issues_in_number_order() -> None:
    issues = [issue(5, ["claimed"]), issue(2, ["priority:now"]), issue(3, ["claimed", "priority:next"])]
    assert next_task.claimed(issues) == ["#3	t3", "#5	t5"]


def test_priority_first_beats_resume_work_and_still_skips_blocked_or_claimed() -> None:
    issues = [
        issue(1, ["resume:1"], created="2026-10-01"),
        issue(2, ["priority:first"], created="2026-11-17"),
        issue(3, ["priority:first", "claimed"], created="2026-11-01"),
        issue(4, ["priority:first"], blocked_by=[1], created="2026-11-01"),
        issue(5, ["priority:now"], created="2026-10-01"),
    ]
    ranked, _ = next_task.rank(issues, ranks={})
    assert numbers(ranked) == [2, 1, 5]
    assert next_task.render(ranked, 5)[0].split("	")[1] == "first"


def test_stale_claim_on_top_ranked_issue_warns_and_names_the_sweep() -> None:
    issues = [issue(1, ["claimed", "resume:1"]), issue(2, ["priority:next"])]
    ranked, _, held = next_task.rank_with_claimed(issues, {})
    assert numbers(ranked) == [2] and numbers(held) == [1]
    lines = next_task.stale_warning(ranked, held, ["release #1 session 544bc8ec is gone"])
    assert len(lines) == 1 and lines[0].startswith("STALE CLAIM? #1: session 544bc8ec is gone")
    assert "claim_sweep.py sweep" in lines[0]


def test_live_claim_or_lower_ranked_claim_gives_no_warning() -> None:
    issues = [issue(1, ["claimed", "resume:1"]), issue(2, ["priority:next"])]
    ranked, _, held = next_task.rank_with_claimed(issues, {})
    assert next_task.stale_warning(ranked, held, ["keep #1 session 544bc8ec is running"]) == []
    low = [issue(1, ["claimed", "priority:later"]), issue(2, ["resume:1"])]
    ranked, _, held = next_task.rank_with_claimed(low, {})
    assert next_task.stale_warning(ranked, held, ["release #1 gone"]) == []
    assert next_task.stale_warning([], [], []) == []


LOW = "GPU lock is free\nmemory free (commit headroom): 2.1 GB; heavy jobs start at 4 GB or more\n"
OK = "GPU lock is free\nmemory free (commit headroom): 14.2 GB; heavy jobs start at 4 GB or more\n"
BUSY = "GPU held by thesis test (pid 1)\nmemory free (commit headroom): 14.2 GB; heavy jobs start at 4 GB or more\n"


def test_machine_clear_reads_memory_gate_and_gpu_lock() -> None:
    assert next_task.machine_clear(OK) == (True, "machine clear")
    assert next_task.machine_clear(LOW)[0] is False and "2.1 GB" in next_task.machine_clear(LOW)[1]
    assert next_task.machine_clear(BUSY)[0] is False


def test_low_memory_skips_heavy_top_issue_takes_light_one_and_names_the_skip() -> None:
    issues = [issue(1, ["resume:1", "heavy"]), issue(2, ["priority:next"]), issue(3, ["resume:2", "heavy"])]
    ranked, _ = next_task.rank(issues, {})
    assert numbers(ranked) == [1, 3, 2]
    clear, reason = next_task.machine_clear(LOW)
    take, skipped = next_task.pick(ranked, clear)
    assert take["number"] == 2 and numbers(skipped) == [1, 3]
    (line,) = next_task.hold_lines(ranked, clear, reason)
    assert line.startswith("HEAVY HOLD:") and "#1, #3" in line and "take #2" in line
    assert "[heavy]" in next_task.render(ranked, 5)[0]


def test_clear_machine_takes_the_top_issue_even_if_heavy_and_no_light_issue_is_named() -> None:
    ranked, _ = next_task.rank([issue(1, ["resume:1", "heavy"]), issue(2)], {})
    assert next_task.pick(ranked, True)[0]["number"] == 1
    assert next_task.hold_lines(ranked, True, "machine clear") == []
    only_heavy, _ = next_task.rank([issue(1, ["heavy"])], {})
    assert "no light issue" in next_task.hold_lines(only_heavy, False, "low")[0]


def test_candidates_record_keeps_top_five_with_tags_and_the_heavy_hold() -> None:
    issues = [issue(n, ["priority:next"], created=f"2026-10-0{n}") for n in range(1, 8)]
    issues[0]["labels"]["nodes"].append({"name": "heavy"})
    ranked, _, _ = next_task.rank_with_claimed(issues)
    rec = next_task.candidates_record("o/r", ranked, False, "free memory 2 GB is under the 4 GB gate", "2026-11-18T01:00:00+00:00")
    assert [c["n"] for c in rec["candidates"]] == [1, 2, 3, 4, 5]
    assert rec["candidates"][0]["tag"] == "next [heavy]"
    assert rec["heavy_hold"] == [1] and rec["default_pick"] == 2
    clear = next_task.candidates_record("o/r", ranked, True, "machine clear", "2026-11-18T01:00:00+00:00")
    assert clear["heavy_hold"] == [] and clear["default_pick"] == 1


def test_append_log_writes_one_json_line_per_call(tmp_path) -> None:
    path = tmp_path / "sub" / "picks.jsonl"
    next_task.append_log({"a": 1}, path)
    next_task.append_log({"a": 2}, path)
    assert path.read_text(encoding="utf-8").splitlines() == ['{"a": 1}', '{"a": 2}']


def test_long_waits_lists_only_starts_that_waited_over_the_threshold() -> None:
    events = [
        {"event": "start", "resource": "gpu", "waited_s": 1500, "purpose": "eval", "cwd": "/r"},
        {"event": "start", "resource": "ram", "waited_s": 599, "purpose": "tests", "cwd": "/r"},
        {"event": "waiting", "resource": "gpu", "waited_s": 9000},
        {"event": "start", "resource": "ram", "waited_s": 0},
    ]
    (line,) = next_task.long_waits(events)
    assert line.startswith("HEAVY EVIDENCE: waited 1500 s on the gpu lock: eval")
    assert next_task.long_waits(events, threshold=599)[1].startswith("HEAVY EVIDENCE: waited 599 s on the ram")
