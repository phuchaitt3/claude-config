import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "stale_claim", Path(__file__).with_name("stale_claim.py")
)
assert _spec and _spec.loader
stale_claim = importlib.util.module_from_spec(_spec)
sys.modules["stale_claim"] = stale_claim
_spec.loader.exec_module(stale_claim)


def states(table):
    calls = []

    def fake(repo, number, cwd):
        calls.append((repo, number))
        value = table[(repo, number)]
        if isinstance(value, Exception):
            raise value
        return value

    fake.calls = calls
    return fake


@pytest.mark.parametrize(
    "line",
    [
        "To do: press **Squash and merge** on [PR #188](https://github.com/o/r/pull/188).",
        "PR #12 needs your merge.",
        "#12 waits for your review.",
        "It is labelled `needs-you`: #12.",
        "You can merge #12 once CI is green.",
    ],
)
def test_action_lines_are_claims(line: str) -> None:
    assert stale_claim.claimed_items(line)


@pytest.mark.parametrize(
    "line",
    [
        "#188 merged at 01:03; #184 closed with it.",
        "Follow-ups stay open: #185, #186, #187.",
        "See commit abc#12 and path a/#3.",
    ],
)
def test_reports_without_an_action_are_not_claims(line: str) -> None:
    assert stale_claim.claimed_items(line) == []


def test_a_url_names_its_repo_and_is_not_counted_twice() -> None:
    items = stale_claim.claimed_items("Press merge on [PR #188](https://github.com/o/r/pull/188).")
    assert items == [("o/r", 188)]


def test_a_merged_item_is_reported() -> None:
    fake = states({(None, 12): ("closed", True)})
    assert stale_claim.stale("PR #12 needs your merge.", ".", fake) == ["#12 is already merged"]


def test_an_open_item_passes() -> None:
    fake = states({(None, 12): ("open", False)})
    assert stale_claim.stale("PR #12 needs your merge.", ".", fake) == []


def test_a_closed_issue_is_reported_as_closed() -> None:
    fake = states({("o/r", 5): ("closed", False)})
    text = "Please review https://github.com/o/r/issues/5"
    assert stale_claim.stale(text, ".", fake) == ["o/r#5 is already closed"]


def test_gh_failure_lets_the_turn_end() -> None:
    fake = states({(None, 12): RuntimeError("no network")})
    assert stale_claim.stale("PR #12 needs your merge.", ".", fake) == []


def test_no_claim_makes_no_gh_call() -> None:
    fake = states({})
    assert stale_claim.stale("All done; tests pass.", ".", fake) == []
    assert fake.calls == []


def test_items_are_capped() -> None:
    text = "Needs your review: " + " ".join(f"#{n}" for n in range(1, 20))
    assert len(stale_claim.claimed_items(text)) == stale_claim.MAX_ITEMS


def test_last_message_reads_the_transcript(tmp_path) -> None:
    transcript = tmp_path / "t.jsonl"
    rows = [
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "old"}]}},
        {"type": "user", "message": {"content": "hi"}},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash"}]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "PR #3 needs your merge."}]}},
    ]
    transcript.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    assert stale_claim.last_message({"transcript_path": str(transcript)}) == "PR #3 needs your merge."
    assert stale_claim.last_message({"last_assistant_message": "x"}) == "x"


def run_main(monkeypatch, capsys, payload, fake) -> str:
    monkeypatch.setattr(stale_claim, "item_state", fake)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    stale_claim.main()
    return capsys.readouterr().out


def test_main_blocks_once_with_a_reason(monkeypatch, capsys) -> None:
    fake = states({(None, 12): ("closed", True)})
    out = run_main(monkeypatch, capsys, {"last_assistant_message": "PR #12 needs your merge."}, fake)
    decision = json.loads(out)
    assert decision["decision"] == "block" and "#12 is already merged" in decision["reason"]


def test_main_never_blocks_twice(monkeypatch, capsys) -> None:
    fake = states({(None, 12): ("closed", True)})
    payload = {"last_assistant_message": "PR #12 needs your merge.", "stop_hook_active": True}
    assert run_main(monkeypatch, capsys, payload, fake) == ""
