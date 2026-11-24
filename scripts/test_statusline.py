import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("statusline", Path(__file__).with_name("statusline.py"))
assert _spec and _spec.loader
statusline = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(statusline)


def test_colour_thresholds() -> None:
    assert statusline.colour(0) == statusline.GREEN
    assert statusline.colour(49.9) == statusline.GREEN
    assert statusline.colour(50) == statusline.YELLOW
    assert statusline.colour(79) == statusline.YELLOW
    assert statusline.colour(80) == statusline.RED


def test_render_shows_model_and_percentage() -> None:
    line = statusline.render({"model": {"display_name": "Opus"}, "context_window": {"used_percentage": 63.4}})
    assert line == f"Opus | {statusline.YELLOW}ctx 63%{statusline.RESET}"


def test_render_without_percentage_shows_only_the_model() -> None:
    assert statusline.render({"model": {"display_name": "Sonnet"}}) == "Sonnet"
    assert statusline.render({}) == ""


def run(stdin: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(Path(__file__).with_name("statusline.py"))],
        input=stdin, capture_output=True, text=True, check=False,
    )


def test_cli_prints_nothing_for_bad_input() -> None:
    for bad in ("", "{ not json", "[1, 2]"):
        result = run(bad)
        assert result.returncode == 0 and result.stdout == ""


def test_cli_prints_the_line() -> None:
    result = run(json.dumps({"context_window": {"used_percentage": 10}}))
    assert result.returncode == 0 and "ctx 10%" in result.stdout


def test_render_shows_the_five_hour_quota() -> None:
    line = statusline.render({"model": {"display_name": "Sonnet"}, "rate_limits": {"five_hour": {"used_percentage": 91.2}}})
    assert line == f"Sonnet | {statusline.RED}5h 91%{statusline.RESET}"


def test_save_quota_writes_rate_limits_with_a_timestamp(tmp_path: Path) -> None:
    path = tmp_path / "q" / "quota.json"
    limits = {"five_hour": {"used_percentage": 40, "resets_at": 123}}
    assert statusline.save_quota({"rate_limits": limits}, path, now=5.0, log=None)
    assert json.loads(path.read_text()) == {"written_at": 5.0, "rate_limits": limits, "age": None}
    assert not statusline.save_quota({}, tmp_path / "other.json")
    assert not (tmp_path / "other.json").exists()


def test_stale_snapshots_do_not_overwrite_the_saved_quota(tmp_path: Path) -> None:
    path = tmp_path / "quota.json"
    now = 1_800_000_000.0
    good = {"five_hour": {"used_percentage": 30, "resets_at": now + 3600},
            "seven_day": {"used_percentage": 24, "resets_at": now + 86400}}
    assert statusline.save_quota({"rate_limits": good}, path, now=now, log=None)
    older = {"five_hour": {"used_percentage": 15, "resets_at": now + 3600},
             "seven_day": {"used_percentage": 19, "resets_at": now + 86400}}
    assert not statusline.save_quota({"rate_limits": older}, path, now=now + 5, log=None)      # lower, same window
    expired = {"five_hour": {"used_percentage": 40, "resets_at": now - 10}}
    assert not statusline.save_quota({"rate_limits": expired}, path, now=now + 5, log=None)    # window already over
    fresh = {"five_hour": {"used_percentage": 2, "resets_at": now + 18000},
             "seven_day": {"used_percentage": 24, "resets_at": now + 86400}}
    assert statusline.save_quota({"rate_limits": fresh}, path, now=now + 3700, log=None)       # new window starts low
    assert json.loads(path.read_text())["rate_limits"] == fresh


def test_reply_age_and_an_old_snapshot_is_stale_whatever_its_value(tmp_path: Path) -> None:
    now = 1_800_000_000.0
    iso = lambda t: __import__("datetime").datetime.fromtimestamp(t, __import__("datetime").timezone.utc).isoformat()
    tr = tmp_path / "t.jsonl"
    tr.write_text("\n".join([
        json.dumps({"timestamp": iso(now - 7200), "message": {"usage": {"output_tokens": 1}}}),
        json.dumps({"timestamp": iso(now - 3), "message": {"role": "user", "content": "hi"}}),  # a prompt, not a reply
    ]), encoding="utf-8")
    assert round(statusline.reply_age(str(tr), now)) == 7200
    assert statusline.reply_age(None, now) is None and statusline.reply_age(str(tmp_path / "no"), now) is None
    limits = {"seven_day": {"used_percentage": 30, "resets_at": now + 86400}}      # higher than saved: value check passes
    assert not statusline.is_stale(limits, {}, now, age=60)
    assert statusline.is_stale(limits, {}, now, age=7200)
    assert not statusline.is_stale(limits, {}, now, age=None)                       # unknown age is trusted


def test_log_quota_writes_the_chat_and_age_and_skips_unchanged(tmp_path: Path) -> None:
    now = 1_800_000_000.0
    log = tmp_path / "log.jsonl"
    limits = {"five_hour": {"used_percentage": 10, "resets_at": now + 600},
              "seven_day": {"used_percentage": 75, "resets_at": now + 86400}}
    assert statusline.log_quota(limits, "s1", 4.2, log, now)
    row = json.loads(log.read_text())
    assert (row["session"], row["age"], row["five"], row["week"], row["week_resets"]) == ("s1", 4, 10, 75, now + 86400)
    assert not statusline.log_quota(limits, "s2", 1, log, now + 60)
    assert statusline.log_quota(limits, "s2", 1, log, now + statusline.LOG_EVERY + 1)
    limits["seven_day"]["used_percentage"] = 76
    assert statusline.log_quota(limits, "s2", 1, log, now + 70)
    assert len(log.read_text().splitlines()) == 3
    assert not statusline.log_quota({}, "s", None, log, now) and not statusline.log_quota(limits, "s", 0, tmp_path / "x" / "..", now)


def test_save_quota_logs_only_accepted_snapshots(tmp_path: Path) -> None:
    now = 1_800_000_000.0
    log = tmp_path / "log.jsonl"
    good = {"seven_day": {"used_percentage": 24, "resets_at": now + 86400}}
    assert statusline.save_quota({"rate_limits": good, "session_id": "a"}, tmp_path / "q.json", now=now, age=3, log=log)
    old = {"seven_day": {"used_percentage": 30, "resets_at": now + 86400}}
    assert not statusline.save_quota({"rate_limits": old, "session_id": "b"}, tmp_path / "q.json", now=now + 1, age=7200, log=log)
    assert [json.loads(x)["session"] for x in log.read_text().splitlines()] == ["a"]
