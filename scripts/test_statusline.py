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
    assert statusline.save_quota({"rate_limits": limits}, path, now=5.0)
    assert json.loads(path.read_text()) == {"written_at": 5.0, "rate_limits": limits}
    assert not statusline.save_quota({}, tmp_path / "other.json")
    assert not (tmp_path / "other.json").exists()
