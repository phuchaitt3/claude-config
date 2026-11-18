import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("picks_log", Path(__file__).with_name("picks_log.py"))
assert _spec and _spec.loader
picks_log = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(picks_log)


def cands(ts, nums, held=(), repo="o/r"):
    return {"event": "candidates", "ts": ts, "repo": repo, "machine": "x", "default_pick": None,
            "candidates": [{"n": n, "tag": "next", "blocks": 0} for n in nums], "heavy_hold": list(held)}


def taken(ts, issue, skipped=None, repo="o/r"):
    return {"event": "taken", "ts": ts, "repo": repo, "issue": issue, "labels": ["priority:next"],
            "skipped": skipped or {}}


def rows(recs):
    return [r for night in picks_log.summarise(recs).values() for r in night]


def test_pick_equal_to_top_ranked_counts_as_a_hit() -> None:
    out = rows([cands("2026-11-18T10:00:00+00:00", [5, 6]), taken("2026-11-18T10:01:00+00:00", 5)])
    assert len(out) == 1 and out[0]["top"] == 5 and out[0]["reason"] is None


def test_heavy_hold_skip_moves_the_top_to_the_first_light_issue() -> None:
    out = rows([cands("2026-11-18T10:00:00+00:00", [5, 6], held=[5]), taken("2026-11-18T10:01:00+00:00", 6)])
    assert out[0]["top"] == 6 and out[0]["reason"] is None and out[0]["heavy_hold"] == [5]


def test_other_pick_carries_the_recorded_reason_or_says_none_recorded() -> None:
    recs = [cands("2026-11-18T10:00:00+00:00", [5, 6]), taken("2026-11-18T10:01:00+00:00", 6, {"5": "needs-you"}),
            cands("2026-11-18T10:10:00+00:00", [7, 8]), taken("2026-11-18T10:11:00+00:00", 8)]
    out = rows(recs)
    assert [r["reason"] for r in out] == ["needs-you", "no reason recorded"]


def test_each_repo_pairs_with_its_own_candidates_line() -> None:
    recs = [cands("2026-11-18T10:00:00+00:00", [1], repo="a/a"), cands("2026-11-18T10:00:30+00:00", [2], repo="b/b"),
            taken("2026-11-18T10:01:00+00:00", 1, repo="a/a")]
    assert rows(recs)[0]["reason"] is None


def test_report_prints_share_and_reasons_and_survives_an_empty_log(tmp_path) -> None:
    recs = [cands("2026-11-18T10:00:00+00:00", [5, 6]), taken("2026-11-18T10:01:00+00:00", 6, {"5": "overlaps a claim"})]
    text = "\n".join(picks_log.report(recs))
    assert "1 picks, 0 were the top-ranked startable issue (0%)" in text and "over #5: overlaps a claim" in text
    assert picks_log.report([]) == ["no picks logged"]
    assert picks_log.load(tmp_path / "missing.jsonl") == []
