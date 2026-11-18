import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import laptop_health as lh


def test_cycles_count_full_swings_and_ignore_wobble():
    assert lh.count_cycles([30, 80, 30, 80, 30]) == 2
    assert lh.count_cycles([60, 62, 58, 61, 63]) == 0
    assert lh.count_cycles([30, 80, 70, 78, 74]) == 0  # one rise, wobble after it
    assert lh.count_cycles([]) == 0
    assert lh.count_cycles([80, 30, 80]) == 1


def test_cycles_respect_the_swing_size():
    assert lh.count_cycles([40, 55, 40, 55, 40], swing_c=10) == 2
    assert lh.count_cycles([40, 55, 40, 55, 40], swing_c=25) == 0


def test_heavy_hours_counts_gpu_or_cpu_load():
    rows = [{"util_pct": 90}, {"cpu_load_pct": 85}, {"util_pct": 10, "cpu_load_pct": 20}, {}]
    assert lh.heavy_hours(rows, 3600) == 2


def test_counter_total_handles_reboot_reset():
    assert lh.total_with_resets([100, 150, 20, 70]) == 50 + 20 + 50
    assert lh.total_with_resets([None, 5, 9]) == 4
    assert lh.total_with_resets([]) == 0


def run(tmp, *args):
    import os

    env = {**os.environ, "GPU_GUARD_DIR": str(tmp)}
    return subprocess.run([sys.executable, str(HERE / "laptop_health.py"), *args], env=env, check=False, capture_output=True, text=True)


def test_report_on_empty_log_does_not_fail(tmp_path):
    r = run(tmp_path, "report")
    assert r.returncode == 0
    assert "no thermal samples" in r.stdout


def test_report_reads_thermal_and_health_logs(tmp_path):
    t = datetime.now().astimezone()
    lines = [{"ts": (t - timedelta(minutes=10)).isoformat(), "event": "start", "interval_s": 60}]
    for i, (g, c, u) in enumerate([(40, 40, 0), (75, 90, 95), (40, 45, 0), (78, 92, 90)]):
        lines.append({"ts": (t - timedelta(minutes=9 - i)).isoformat(), "event": "sample", "gpu_temp_c": g,
                      "cpu_temp_c": c, "util_pct": u, "cpu_load_pct": u})
    (tmp_path / "thermal.jsonl").write_text("\n".join(json.dumps(x) for x in lines))
    snaps = [{"ts": (t - timedelta(hours=2)).isoformat(), "event": "snapshot", "disk": {"written_bytes": 100e9},
              "battery": {"design_mwh": 57000, "full_mwh": 44600, "cycles": 618},
              "events_since_last": {"whea": 0, "kernel_power_41": 0}, "disks": {"reliability_note": "no counters"}},
             {"ts": t.isoformat(), "event": "snapshot", "disk": {"written_bytes": 112e9},
              "battery": {"design_mwh": 57000, "full_mwh": 44500, "cycles": 619},
              "events_since_last": {"whea": 1, "kernel_power_41": 0}, "disks": {"reliability_note": "no counters"}}]
    (tmp_path / "health.jsonl").write_text("\n".join(json.dumps(x) for x in snaps))
    out = run(tmp_path, "report").stdout
    assert "heavy (>= 80% load)" in out
    assert "heat-cool cycles (swing >= 25 C): 1" in out
    assert "written, all disks (Windows counter, includes the HDD): 12.0 GB" in out
    assert "WHEA): 1" in out
    assert "44600 -> 44500" in out


def test_due_exits_1_without_a_reference_and_0_after(tmp_path):
    assert run(tmp_path, "due").returncode == 1
    (tmp_path / "health.jsonl").write_text(json.dumps({"ts": datetime.now().astimezone().isoformat(), "event": "reference"}))
    assert run(tmp_path, "due").returncode == 0


def test_parse_smart_nvme_and_ata():
    nv = lh.parse_smart({"device": {"name": "/dev/sdb", "type": "nvme"}, "model_name": "SSD", "smart_status": {"passed": True},
                         "nvme_smart_health_information_log": {"percentage_used": 25, "data_units_written": 2,
                                                               "unsafe_shutdowns": 201, "temperature": 47}})
    assert nv["written_bytes"] == 1024000 and nv["percentage_used"] == 25 and nv["passed"] is True
    ata = lh.parse_smart({"device": {"name": "/dev/sda"}, "smart_status": {"passed": True},
                          "ata_smart_attributes": {"table": [{"id": 5, "raw": {"value": 0}},
                                                             {"id": 9, "raw": {"value": 230455060218021}}]},
                          "power_on_time": {"hours": 16549}, "temperature": {"current": 37}})
    assert ata["power_on_hours"] == 16549 and ata["temperature_c"] == 37 and ata["reallocated_sectors"] == 0


def test_smart_lines_show_ssd_writes_and_changes():
    snaps = [{"disks": {"smart": [{"model": "SSD", "passed": True, "written_bytes": 10e9, "percentage_used": 25}]}},
             {"disks": {"smart": [{"model": "SSD", "passed": True, "written_bytes": 13e9, "percentage_used": 26}]}}]
    line = lh.smart_lines(snaps)[0]
    assert "written 3.0 GB" in line and "wear % 25 -> 26" in line and "PASSED" in line
    assert "not read" in lh.smart_lines([{}])[0]


def test_room_proxy_prefers_the_hdd():
    smart = [{"type": "nvme", "temperature_c": 47}, {"type": "ata", "temperature_c": 37}]
    assert lh.room_proxy(smart) == 37
    assert lh.room_proxy([{"type": "nvme", "temperature_c": 45}]) == 45
    assert lh.room_proxy([]) is None


def test_report_marks_a_reference_from_an_unusual_room(tmp_path):
    now = datetime.now().astimezone()
    refs = [{"ts": (now - timedelta(days=d)).isoformat(), "event": "reference", "room_proxy_c": c, "cpu_temp_c": 70}
            for d, c in ((21, 36), (14, 37), (7, 31))]
    (tmp_path / "health.jsonl").write_text("\n".join(json.dumps(x) for x in refs))
    out = run(tmp_path, "report").stdout
    assert out.count("not comparable") == 1 and "room 31 C vs usual 36 C" in out


# ---------------------------------------------------------------------------- cap benchmark (#23)

import gpu_cap_bench as gcb  # noqa: E402


def _bench_row(days_ago, driver="1", setting="1350", mhz=1350, temp=60.0, tps=50.0, cooling="flat", bench="a", ac=True):
    ts = (datetime.now().astimezone() - timedelta(days=days_ago)).isoformat(timespec="seconds")
    return {"ts": ts, "event": "cap_bench", "bench_id": bench, "setting": setting, "clock_mhz": mhz, "temp_c": temp,
            "tokens_s": tps, "power_w": 40.0, "tokens_per_joule": 1.2, "stable": True, "driver": driver, "cooling": cooling, "ac": ac}


def _write(tmp, rows):
    (tmp / "health.jsonl").write_text("\n".join(json.dumps(r) for r in rows))


def test_cap_bench_due_none_old_and_driver_change():
    assert "no cap benchmark" in lh.cap_bench_due([], 30, "1")
    assert lh.cap_bench_due([_bench_row(3)], 30, "1") is None
    assert "driver changed" in lh.cap_bench_due([_bench_row(3)], 30, "2")
    assert lh.cap_bench_due([_bench_row(3)], 30, None) is None  # driver unreadable: not a reason


def test_due_cap_bench_exit_codes(tmp_path):
    assert run(tmp_path, "due", "--kind", "cap-bench").returncode in (1, 2)  # 2 only if this machine is on battery
    _write(tmp_path, [_bench_row(40)])
    assert run(tmp_path, "due", "--kind", "cap-bench").returncode in (1, 2)  # older than 30 days
    assert run(tmp_path, "due", "--kind", "cap-bench", "--days", "60").returncode in (0, 1, 2)


def test_stability_needs_time_requests_flat_temperature_and_steady_speed():
    flat = [(s, 60.0 + (0.3 if s % 2 else 0)) for s in range(0, 100, 2)]
    steady = [50.0, 50.2, 49.9, 50.1, 50.0]
    assert gcb.is_stable(100, flat, steady)
    assert not gcb.is_stable(50, flat, steady)  # before 60 s
    assert not gcb.is_stable(100, flat, steady[:4])  # fewer than 5 requests
    assert not gcb.is_stable(100, flat, [50, 52, 48, 51, 49])  # CV above 2%
    rising = [(s, 55 + s * 0.05) for s in range(0, 100, 2)]
    assert not gcb.is_stable(100, rising, steady)  # the mean drifts 1.5 C between the two halves
    fan = [(s, 58.0 if (s // 2) % 2 else 62.0) for s in range(0, 100, 2)]
    assert gcb.is_stable(100, fan, steady)  # swinging 4 C but not drifting: stable


def test_summarise_uses_the_last_window_and_tokens_per_joule():
    samples = [{"s": s, "gpu_temp_c": 60.0, "power_w": 40.0, "sm_mhz": 1350} for s in range(0, 100, 2)]
    r = gcb.summarise(100, samples, [48, 50, 50, 50, 50, 50], True)
    assert r["temp_c"] == 60.0 and r["power_w"] == 40.0 and r["sm_mhz_max"] == 1350
    assert r["tokens_s"] == 50.0 and r["tokens_per_joule"] == 1.25 and r["stable"]
    assert r["temp_range_c"] == 0.0 and r["tps_cv_pct"] is not None


def test_cap_task_names():
    assert gcb.task_for(1200) == "gpu-clock-cap-1200" and gcb.task_for(1350) == "gpu-clock-cap-on" and gcb.task_for(None) == "gpu-clock-cap-off"


def test_report_table_best_setting_and_same_cooling_comparison(tmp_path):
    def group(days, bench, cooling, t1350, ac=True):
        return [_bench_row(days, setting="1200", mhz=1200, temp=t1350 - 2, tps=42, bench=bench, cooling=cooling, ac=ac),
                _bench_row(days, setting="1350", mhz=1350, temp=t1350, tps=46, bench=bench, cooling=cooling, ac=ac),
                _bench_row(days, setting="uncapped", mhz=None, temp=t1350 + 9, tps=54, bench=bench, cooling=cooling, ac=ac)]
    lines = "\n".join(lh.cap_bench_lines(group(40, "a", "flat", 60) + group(1, "b", "flat", 62)))
    assert "against" in lines and "+2.0 C" in lines
    assert "1350 is still the best" in lines  # 1200 is cooler but 42 tok/s is under 80% of 54
    unsettled = [dict(r, stable=False) for r in group(20, "u", "flat", 50)]
    lines = "\n".join(lh.cap_bench_lines(unsettled + group(1, "b", "flat", 62)))
    assert "new baseline" in lines  # an unsettled run is not compared against
