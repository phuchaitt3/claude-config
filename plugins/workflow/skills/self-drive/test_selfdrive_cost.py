import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

_spec = importlib.util.spec_from_file_location("selfdrive_cost", Path(__file__).with_name("selfdrive_cost.py"))
cost = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cost)

T0 = 1_800_000_000


def _iso(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat()


def _log(tmp_path, rows):
    p = tmp_path / "q.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows))
    return p


def _row(t, week, five=0, wr=9e9, fr=9e9):
    return {"t": t, "week": week, "week_resets": wr, "five": five, "five_resets": fr}


def test_sums_rises_from_the_sample_before_the_window(tmp_path):
    p = _log(tmp_path, [_row(T0 - 100, 70), _row(T0 + 10, 72, 5), _row(T0 + 20, 75, 9)])
    q = cost.quota_used(p, _iso(T0), _iso(T0 + 50))
    assert q["week_pct"] == 5 and q["five_pct"] == 9 and q["week_end"] == 75 and q["quota_samples"] == 2


def test_a_reset_adds_nothing(tmp_path):
    p = _log(tmp_path, [_row(T0 - 5, 90, 80), _row(T0 + 10, 2, 1, wr=9e9 + 1, fr=9e9 + 1), _row(T0 + 20, 4, 3, wr=9e9 + 1, fr=9e9 + 1)])
    q = cost.quota_used(p, _iso(T0), _iso(T0 + 50))
    assert q["week_pct"] == 2 and q["five_pct"] == 2


def test_none_without_log_or_samples(tmp_path):
    assert cost.quota_used(tmp_path / "none", _iso(T0), _iso(T0 + 1)) is None
    assert cost.quota_used(_log(tmp_path, [_row(T0 - 9, 1)]), _iso(T0), _iso(T0 + 1)) is None


def _tok(sonnet_in=0, opus_out=0):
    z = dict.fromkeys(cost.KINDS, 0)
    return {"s": {**z, "input_tokens": sonnet_in}, "o": {**z, "output_tokens": opus_out}}


def test_calibrate_divides_tokens_by_weekly_rise(tmp_path, monkeypatch):
    monkeypatch.setattr(cost, "tokens_by_interval", lambda spans: [_tok(sonnet_in=10_000_000) for _ in spans])
    c = cost.calibrate(_log(tmp_path, [_row(T0, 50), _row(T0 + 99, 60)]), store=tmp_path / "iv.jsonl")
    assert c["M_per_week_pct"] == 1.0 and c["week_cap_M"] == 100


def test_calibrate_saves_intervals_by_model_and_kind_and_survives_deleted_transcripts(tmp_path, monkeypatch):
    store = tmp_path / "iv.jsonl"
    log = _log(tmp_path, [_row(T0, 50), _row(T0 + 99, 60)])
    monkeypatch.setattr(cost, "tokens_by_interval", lambda spans: [_tok(sonnet_in=8_000_000, opus_out=400_000) for _ in spans])
    first = cost.calibrate(log, store=store)
    saved = json.loads(store.read_text())
    assert saved["tokens"]["o"]["output_tokens"] == 400_000 and saved["tokens"]["s"]["input_tokens"] == 8_000_000
    assert (saved["week0"], saved["week1"]) == (50, 60)
    monkeypatch.setattr(cost, "tokens_by_interval", lambda spans: 1 / 0)  # transcripts gone: must not be needed
    assert cost.calibrate(log, store=store) == first
    assert len(store.read_text().splitlines()) == 1


def test_calibrate_needs_a_real_rise(tmp_path, monkeypatch):
    monkeypatch.setattr(cost, "tokens_by_interval", lambda spans: [_tok(1) for _ in spans])
    assert cost.calibrate(_log(tmp_path, [_row(T0, 50), _row(T0 + 9, 53)]), store=tmp_path / "iv.jsonl") is None
    assert cost.calibrate(tmp_path / "none", store=tmp_path / "iv.jsonl") is None


def test_tokens_by_interval_splits_by_model_and_ignores_duplicates(tmp_path, monkeypatch):
    def msg(i, model, t, **u):
        return {"timestamp": _iso(t), "message": {"id": i, "model": model, "usage": u}}
    proj = tmp_path / ".claude" / "projects" / "p"
    proj.mkdir(parents=True)
    rows = [msg("a", "sonnet", T0 + 5, input_tokens=10, output_tokens=1), msg("a", "sonnet", T0 + 5, input_tokens=10),
            msg("b", "opus", T0 + 6, output_tokens=7), msg("c", "opus", T0 + 500, output_tokens=9)]
    (proj / "x.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    monkeypatch.setattr(cost.os.path, "expanduser", lambda p: str(tmp_path))
    out = cost.tokens_by_interval([(T0, T0 + 10)])[0]
    assert out["sonnet"]["input_tokens"] == 10 and out["sonnet"]["output_tokens"] == 1 and out["opus"]["output_tokens"] == 7


def test_clean_drops_stale_quota_readings():
    rows = [
        dict(t=100, week=20.0, week_resets=9e9, five=10.0, five_resets=5000),
        dict(t=200, week=24.0, week_resets=9e9, five=30.0, five_resets=5000),
        dict(t=300, week=19.0, week_resets=9e9, five=15.0, five_resets=5000),   # idle chat: lower, same window
        dict(t=400, week=19.0, week_resets=9e9),                                  # lower weekly, no 5-hour block
        dict(t=6000, week=24.0, week_resets=9e9, five=2.0, five_resets=23000),     # new window starts low: kept
        dict(t=6100, week=22.0, week_resets=9e9, five=40.0, five_resets=5000),     # old window already over
    ]
    assert [r["t"] for r in cost.clean(rows)] == [100, 200, 6000]
