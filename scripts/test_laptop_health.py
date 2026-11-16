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
