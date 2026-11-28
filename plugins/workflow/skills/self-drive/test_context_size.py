import importlib.util
import json
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cs = _load("context_size")
cr = _load("context_report")


def _write_transcript(path, ctxs, edit_at=1, error_at=2):
    lines = []
    for i, ctx in enumerate(ctxs):
        tool = {"type": "tool_use", "id": f"t{i}", "name": "Edit" if i == edit_at else "Bash"}
        usage = {"input_tokens": 0, "cache_read_input_tokens": ctx - 1000, "cache_creation_input_tokens": 1000, "output_tokens": 100}
        lines.append({"type": "assistant", "timestamp": f"2026-11-15T00:0{i}:00Z", "requestId": f"r{i}",
                      "message": {"content": [tool], "usage": usage}})
        lines.append({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": f"t{i}", "is_error": i == error_at}]}})
    path.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")


def test_stats_and_handover_mark(tmp_path) -> None:
    p = tmp_path / "s.jsonl"
    _write_transcript(p, [55000, 100000, 160000])
    turns, errors, first_ts = cs.read_turns(str(p))
    rec = cs.record("sid", str(p), turns, errors, first_ts, 150000)
    assert rec["ctx_now"] == 160000 and rec["event"] == "handover"
    assert rec["turns"] == 3 and rec["tool_calls"] == 3 and rec["tool_errors"] == 1
    assert rec["turns_to_first_edit"] == 1
    assert rec["by_ctx_bin"]["150"]["errors"] == 1
    assert cs.record("sid", str(p), turns, errors, first_ts, 200000)["event"] == "round"


def test_report_uses_last_line_and_keeps_handover(tmp_path) -> None:
    p = tmp_path / "s.jsonl"
    _write_transcript(p, [55000, 100000, 160000])
    turns, errors, first_ts = cs.read_turns(str(p))
    log = tmp_path / "log.jsonl"
    early = cs.record("sid", str(p), turns[:2], errors, first_ts, 150000)
    late = cs.record("sid", str(p), turns, errors, first_ts, 150000)
    log.write_text(json.dumps(late) + "\n" + json.dumps(early) + "\n", encoding="utf-8")
    recs = cr.load(str(log))
    assert len(recs) == 1 and recs[0]["handed_over"] is True
    s = cr.summarise(recs)
    assert s["sessions"] == 1 and s["F"] == 55000


def test_note_is_written_to_the_log_line(tmp_path, monkeypatch) -> None:
    p = tmp_path / "s.jsonl"
    _write_transcript(p, [55000])
    log = tmp_path / "log.jsonl"
    monkeypatch.setattr(cs, "LOG", str(log))
    monkeypatch.setattr(cs.glob, "glob", lambda _pattern: [str(p)])
    assert cs.main(["sid", "--log", "--note", "issue done"]) == 0
    assert json.loads(log.read_text(encoding="utf-8"))["note"] == "issue done"
