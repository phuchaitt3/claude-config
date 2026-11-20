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


def _row(t, week, five=0, wr=9, fr=5):
    return {"t": t, "week": week, "week_resets": wr, "five": five, "five_resets": fr}


def test_sums_rises_from_the_sample_before_the_window(tmp_path):
    p = _log(tmp_path, [_row(T0 - 100, 70), _row(T0 + 10, 72, 5), _row(T0 + 20, 75, 9)])
    q = cost.quota_used(p, _iso(T0), _iso(T0 + 50))
    assert q["week_pct"] == 5 and q["five_pct"] == 9 and q["week_end"] == 75 and q["quota_samples"] == 2


def test_a_reset_adds_nothing(tmp_path):
    p = _log(tmp_path, [_row(T0 - 5, 90, 80), _row(T0 + 10, 2, 1, wr=10, fr=6), _row(T0 + 20, 4, 3, wr=10, fr=6)])
    q = cost.quota_used(p, _iso(T0), _iso(T0 + 50))
    assert q["week_pct"] == 2 and q["five_pct"] == 2


def test_none_without_log_or_samples(tmp_path):
    assert cost.quota_used(tmp_path / "none", _iso(T0), _iso(T0 + 1)) is None
    assert cost.quota_used(_log(tmp_path, [_row(T0 - 9, 1)]), _iso(T0), _iso(T0 + 1)) is None


def test_calibrate_divides_tokens_by_weekly_rise(tmp_path, monkeypatch):
    monkeypatch.setattr(cost, "weighted_between", lambda a, b: 10e6)
    p = _log(tmp_path, [_row(T0, 50), _row(T0 + 99, 60)])
    c = cost.calibrate(p)
    assert c["M_per_week_pct"] == 1.0 and c["week_cap_M"] == 100


def test_calibrate_needs_a_real_rise(tmp_path, monkeypatch):
    monkeypatch.setattr(cost, "weighted_between", lambda a, b: 10e6)
    assert cost.calibrate(_log(tmp_path, [_row(T0, 50), _row(T0 + 9, 53)])) is None
    assert cost.calibrate(tmp_path / "none") is None
