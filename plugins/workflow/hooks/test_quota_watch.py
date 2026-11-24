import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("quota_watch", Path(__file__).with_name("quota_watch.py"))
assert _spec and _spec.loader
quota_watch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(quota_watch)

NOW = 1_800_000_000.0


def _write(tmp_path: Path, used: float, resets: float, written: float = NOW) -> Path:
    path = tmp_path / "quota.json"
    record = {"written_at": written, "rate_limits": {"five_hour": {"used_percentage": used, "resets_at": resets}}}
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def test_reads_a_fresh_file(tmp_path: Path) -> None:
    assert quota_watch.read_quota(_write(tmp_path, 92.5, NOW + 600), now=NOW) == (92.5, NOW + 600)


def test_missing_broken_stale_or_past_reset_is_none(tmp_path: Path) -> None:
    assert quota_watch.read_quota(tmp_path / "none.json", now=NOW) is None
    bad = tmp_path / "bad.json"
    bad.write_text("{")
    assert quota_watch.read_quota(bad, now=NOW) is None
    assert quota_watch.read_quota(_write(tmp_path, 95, NOW + 600, written=NOW - 3600), now=NOW) is None
    assert quota_watch.read_quota(_write(tmp_path, 95, NOW - 1), now=NOW) is None


def test_silent_below_threshold() -> None:
    assert quota_watch.message(89.9, NOW + 600, NOW) == ""


def test_at_threshold_names_the_pause_and_caps_the_wakeup() -> None:
    text = quota_watch.message(90, NOW + 7200, NOW)
    assert "Quota pause" in text and "sleep 7320" in text and "delaySeconds=3600" in text
    short = quota_watch.message(97, NOW + 600, NOW)
    assert "sleep 720" in short and "delaySeconds=720" in short


def test_hook_prints_nothing_without_a_quota_file(tmp_path: Path) -> None:
    out = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("quota_watch.py"))],
        input=json.dumps({"hook_event_name": "UserPromptSubmit"}),
        capture_output=True,
        text=True,
        env={"HOME": str(tmp_path), "USERPROFILE": str(tmp_path)},
        check=True,
    )
    assert out.stdout == ""


def test_registered_in_hooks_json() -> None:
    hooks = json.loads(Path(__file__).with_name("hooks.json").read_text(encoding="utf-8"))
    commands = [h["command"] for group in hooks["hooks"]["UserPromptSubmit"] for h in group["hooks"]]
    assert any("quota_watch.py" in c for c in commands)
