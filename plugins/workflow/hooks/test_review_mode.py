import importlib.util
import json
import re
from pathlib import Path

_spec = importlib.util.spec_from_file_location("review_mode", Path(__file__).with_name("review_mode.py"))
assert _spec and _spec.loader
review_mode = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(review_mode)

REPO = Path(__file__).resolve().parents[3]


def _write(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "review.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_reads_a_valid_mode(tmp_path: Path) -> None:
    mode, line = review_mode.read_mode(_write(tmp_path, {"mode": "self-diff", "since": "2026-11-01", "why": "quota"}))
    assert mode == "self-diff" and "since 2026-11-01" in line and "quota" in line


def test_missing_broken_or_unknown_falls_back_to_peer(tmp_path: Path) -> None:
    assert review_mode.read_mode(tmp_path / "none.json")[0] == "peer"
    bad = tmp_path / "bad.json"
    bad.write_text("{")
    assert review_mode.read_mode(bad)[0] == "peer"
    mode, line = review_mode.read_mode(_write(tmp_path, {"mode": "off"}))
    assert mode == "peer" and "fallback" in line


def test_session_start_always_announces() -> None:
    told, text = review_mode.decide("SessionStart", "Review mode: peer.", "peer", "Review mode: peer.")
    assert told == "Review mode: peer." and "workflow:pr-review" in text


def test_prompt_announces_only_a_change() -> None:
    _, same = review_mode.decide("UserPromptSubmit", "Review mode: peer.", "peer", "Review mode: peer.")
    assert same == ""
    told, changed = review_mode.decide("UserPromptSubmit", "Review mode: peer.", "ci-only", "Review mode: ci-only.")
    assert told == "Review mode: ci-only." and "ci-only" in changed


def test_a_session_never_told_is_told_on_its_first_prompt() -> None:
    _, text = review_mode.decide("UserPromptSubmit", None, "self-diff", "Review mode: self-diff.")
    assert "self-diff" in text


def test_the_shipped_setting_is_valid() -> None:
    mode, line = review_mode.read_mode(REPO / "settings" / "review.json")
    assert mode in review_mode.MODES and "fallback" not in line


def test_the_skill_table_names_exactly_the_hook_modes() -> None:
    skill = (REPO / "plugins" / "workflow" / "skills" / "pr-review" / "SKILL.md").read_text(encoding="utf-8")
    section = skill.split("## Review modes", 1)[1].split("\n## ", 1)[0]
    in_table = tuple(re.findall(r"^\| `([a-z-]+)` \|", section, flags=re.M))
    assert in_table == review_mode.MODES
