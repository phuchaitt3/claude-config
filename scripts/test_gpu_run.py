import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCRIPT = str(HERE / "gpu_run.py")


def run(tmp, *args, **kw):
    env = {**ENV(tmp), **kw.pop("extra_env", {})}
    return subprocess.run([sys.executable, SCRIPT, *args], env=env, capture_output=True, text=True, **kw)


import pytest


@pytest.fixture(autouse=True)
def _no_inherited_lock_markers(monkeypatch):
    """In-process tests read os.environ: drop the "lock held" markers a suite run under gpu_run.py inherits."""
    import os
    for k in [k for k in os.environ if "_HELD" in k]:
        monkeypatch.delenv(k)


def ENV(tmp):
    # admission off by default in tests: the machine's real free memory must not decide a test
    # a suite started inside `gpu_run.py run` inherits its "lock held" markers, which would make the tests
    # skip the locks they check: drop them, so the whole suite can run under the RAM lock
    env = {k: v for k, v in __import__("os").environ.items() if "_HELD" not in k}
    return {**env, "GPU_GUARD_DIR": str(tmp), "OLLAMA_HOST": "127.0.0.1:1",
            "GPU_RUN_MIN_FREE_GB": "0"}


def events(tmp, res=None):
    ev = [json.loads(x) for x in (tmp / "events.jsonl").read_text().splitlines()]
    if res is None:
        return ev
    return [e for e in ev if e.get("resource", "gpu") == res or (res == "gpu" and "resource" not in e)]


def test_runs_command_logs_and_forwards_exit_code(tmp_path):
    r = run(tmp_path, "run", "--purpose", "t", "--", sys.executable, "-c", "raise SystemExit(7)")
    assert r.returncode == 7
    ev = events(tmp_path)
    # a GPU job takes the RAM lock first and releases it last (user's decision, 2026-11-17)
    assert [(e["event"], e["resource"]) for e in ev] == [("start", "ram"), ("start", "gpu"),
                                                         ("end", "gpu"), ("end", "ram")]
    assert ev[2]["exit_code"] == 7 and ev[3]["exit_code"] == 7
    assert "mem_free_gb" in ev[0]


def test_child_sees_held_by_and_lock_is_free_after(tmp_path):
    code = "import os;print(os.environ['GPU_GUARD_HELD_BY'])"
    r = run(tmp_path, "run", "--", sys.executable, "-c", code)
    assert r.stdout.strip().isdigit()
    assert "free" in run(tmp_path, "status").stdout


def test_second_job_is_refused_and_logged(tmp_path):
    holder = subprocess.Popen(
        [sys.executable, SCRIPT, "run", "--purpose", "first", "--", sys.executable, "-c",
         "import time;time.sleep(6)"],
        env=ENV(tmp_path),
    )
    try:
        import time
        for _ in range(40):
            if "held" in run(tmp_path, "status").stdout:
                break
            time.sleep(0.25)
        r = run(tmp_path, "run", "--purpose", "second", "--", sys.executable, "-c", "pass")
        assert r.returncode == 3 and "first" in r.stderr
        assert any(e["event"] == "refused" for e in events(tmp_path))
        # the first job holds RAM too, so the second is refused there, before it asks for the GPU
        assert "refused (lock taken, did not wait): 1" in run(tmp_path, "report", "--resource", "ram").stdout
    finally:
        holder.wait()


def _module():
    import os
    os.environ["GPU_RUN_MIN_FREE_GB"] = "0"
    import importlib.util
    spec = importlib.util.spec_from_file_location("gpu_run_mod", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_classify_names_ollama_only_when_it_accounts_for_the_memory():
    g = _module()
    busy = {"util_pct": 50.0, "mem_mb": 3000.0}
    assert g.classify(None, False, 0) == "none"
    assert g.classify(busy, True, 0) == "guarded"
    assert g.classify({"util_pct": 0.0, "mem_mb": 100.0}, False, 0) == "idle"
    assert g.classify(busy, False, 2900) == "ollama"
    assert g.classify(busy, False, 1000) == "unguarded"
    assert g.classify(busy, False, 0) == "unguarded"
    # the desktop alone (display, browser, overlay) is not a job: 1.5 GB at 4% busy is idle (2026-11-23)
    assert g.classify({"util_pct": 4.0, "mem_mb": 1553.0}, False, 0) == "idle"
    assert g.classify({"util_pct": 4.0, "mem_mb": 2500.0}, False, 0) == "unguarded"


def test_hold_keeps_lock_until_its_containers_stop(tmp_path, monkeypatch):
    import argparse
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(g, "HOLD_POLL_SECONDS", 0)
    monkeypatch.setattr(g, "ollama_models", lambda: [])
    seen = {"status_while_held": None}
    calls = iter([{"old": "other"}, {"old": "other", "new": "rr"}, {"old": "other", "new": "rr"}, {"old": "other"}])

    def fake_containers(gpu_only=True):
        c = next(calls)
        if c == {"old": "other", "new": "rr"} and seen["status_while_held"] is None:
            seen["status_while_held"] = (g.Lock().is_held(), g.Lock("ram").is_held())
        return c

    monkeypatch.setattr(g, "containers", fake_containers)
    monkeypatch.setattr(g, "containers_mem_mb", lambda ids: 1500.0 if ids else 0.0)
    args = argparse.Namespace(command=["--", sys.executable, "-c", "pass"], purpose="svc", wait=False,
                              keep_ollama=False)
    assert g.cmd_hold(args) == 0
    assert seen["status_while_held"] == (True, True)  # a GPU hold keeps the RAM lock too
    assert not g.Lock().is_held() and not g.Lock("ram").is_held()
    ev = events(tmp_path)
    assert [e["event"] for e in ev] == ["start", "start", "hold", "end", "end"]
    assert ev[2]["containers"] == ["rr"] and ev[3]["kind"] == "service"
    assert ev[3]["peak_stack_mem_mb"] == 1500.0


def test_hold_releases_when_no_new_container(tmp_path, monkeypatch):
    import argparse
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(g, "ollama_models", lambda: [])
    monkeypatch.setattr(g, "containers", lambda gpu_only=True: {"old": "other"})
    args = argparse.Namespace(command=[sys.executable, "-c", "pass"], purpose="svc", wait=False,
                              keep_ollama=False)
    assert g.cmd_hold(args) == 0
    assert [e["event"] for e in events(tmp_path)] == ["start", "start", "end", "end"]
    assert not g.Lock().is_held() and not g.Lock("ram").is_held()


def test_hold_stops_containers_at_the_deadline(tmp_path, monkeypatch):
    import argparse
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(g, "HOLD_POLL_SECONDS", 0)
    monkeypatch.setattr(g, "ollama_models", lambda: [])
    state = {"n": 0, "stopped": None}

    def fake_containers(gpu_only=True):
        state["n"] += 1
        return {} if state["n"] == 1 else {"new": "rr"}

    def fake_stop(ids):
        state["stopped"] = ids
        return True

    monkeypatch.setattr(g, "containers", fake_containers)
    monkeypatch.setattr(g, "containers_mem_mb", lambda ids: 0.0)
    monkeypatch.setattr(g, "stop_containers", fake_stop)
    args = argparse.Namespace(command=[sys.executable, "-c", "pass"], purpose="svc", wait=False,
                              keep_ollama=False, max_minutes=1e-9)
    assert g.cmd_hold(args) == 124
    assert state["stopped"] == ["new"]
    assert [e["event"] for e in events(tmp_path)] == ["start", "start", "hold", "deadline", "end", "end"]
    assert not g.Lock().is_held()


def test_taking_the_lock_unloads_ollama_models_and_logs_each(tmp_path, monkeypatch):
    import argparse
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    unloaded = []
    monkeypatch.setattr(g, "ollama_models", lambda: [{"name": "qwen3:4b", "vram_mb": 3900},
                                                     {"name": "cpu-only", "vram_mb": 0}])
    monkeypatch.setattr(g, "ollama_unload", lambda name: unloaded.append(name) or True)
    args = argparse.Namespace(command=[sys.executable, "-c", "pass"], purpose="job", wait=False,
                              keep_ollama=False)
    assert g.cmd_run(args) == 0
    assert unloaded == ["qwen3:4b"]
    ev = events(tmp_path, "gpu")
    assert [e["event"] for e in ev] == ["start", "ollama_unload", "end"]
    assert ev[1]["model"] == "qwen3:4b" and ev[1]["ok"] is True


def test_keep_ollama_lists_but_does_not_unload(tmp_path, monkeypatch, capsys):
    import argparse
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(g, "ollama_models", lambda: [{"name": "qwen3:4b", "vram_mb": 3900}])

    def boom(name):
        raise AssertionError("unloaded")

    monkeypatch.setattr(g, "ollama_unload", boom)
    args = argparse.Namespace(command=[sys.executable, "-c", "pass"], purpose="job", wait=False,
                              keep_ollama=True)
    assert g.cmd_run(args) == 0
    assert "left loaded" in capsys.readouterr().err
    assert [e["event"] for e in events(tmp_path, "gpu")] == ["start", "end"]


def test_failed_unload_is_logged_and_said_but_the_job_still_runs(tmp_path, monkeypatch, capsys):
    import argparse
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(g, "ollama_models", lambda: [{"name": "m", "vram_mb": 100}])
    monkeypatch.setattr(g, "ollama_unload", lambda name: False)
    args = argparse.Namespace(command=[sys.executable, "-c", "pass"], purpose="job", wait=False,
                              keep_ollama=False)
    assert g.cmd_run(args) == 0
    assert "could not unload m" in capsys.readouterr().err
    assert events(tmp_path, "gpu")[1]["ok"] is False


def test_old_stop_ollama_flag_is_still_accepted(tmp_path):
    r = run(tmp_path, "run", "--stop-ollama", "--", sys.executable, "-c", "pass")
    assert r.returncode == 0


def test_a_gpu_job_needs_the_ram_lock_unless_its_parent_holds_it(tmp_path):
    import time
    holder = subprocess.Popen(
        [sys.executable, SCRIPT, "run", "--resource", "ram", "--purpose", "suite", "--", sys.executable, "-c",
         "import time;time.sleep(6)"],
        env=ENV(tmp_path),
    )
    try:
        for _ in range(40):
            if "held" in run(tmp_path, "status", "--resource", "ram").stdout:
                break
            time.sleep(0.25)
        assert "RAM held by suite" in run(tmp_path, "status", "--resource", "ram").stdout
        assert "GPU lock is free" in run(tmp_path, "status").stdout  # the GPU lock is untouched
        gpu = run(tmp_path, "run", "--purpose", "model", "--", sys.executable, "-c", "pass")
        assert gpu.returncode == 3 and "RAM/CPU lock is in use by suite" in gpu.stderr
        nested = run(tmp_path, "run", "--", sys.executable, "-c", "pass",
                     extra_env={"GPU_GUARD_RAM_HELD_BY": "1"})  # inside `run --resource ram`: GPU lock only
        assert nested.returncode == 0
        second = run(tmp_path, "run", "--resource", "ram", "--purpose", "build", "--", sys.executable, "-c", "pass")
        assert second.returncode == 3 and "RAM/CPU lock is in use by suite" in second.stderr
        out = run(tmp_path, "report", "--resource", "ram").stdout
        assert "refused (lock taken, did not wait): 2" in out
        assert "refused (GPU taken, did not wait): 0" in run(tmp_path, "report").stdout
    finally:
        holder.wait()
    assert (tmp_path / "local-ram.lock").exists() and (tmp_path / "local-gpu.lock").exists()


def test_ram_job_logs_its_resource_gets_its_own_env_and_skips_ollama(tmp_path):
    code = "import os;print(os.environ['GPU_GUARD_RAM_HELD_BY'])"
    r = run(tmp_path, "run", "--resource", "ram", "--", sys.executable, "-c", code)
    pid = r.stdout.split()[0]
    assert pid.isdigit()
    ev = events(tmp_path)
    assert [e["event"] for e in ev] == ["start", "end"] and {e["resource"] for e in ev} == {"ram"}
    assert "peak_gpu_mem_mb" not in ev[1] or ev[1]["peak_gpu_mem_mb"] is None


def test_ram_report_counts_only_ram_jobs_and_gpu_report_only_gpu_jobs(tmp_path):
    run(tmp_path, "run", "--resource", "ram", "--", sys.executable, "-c", "pass")
    run(tmp_path, "run", "--", sys.executable, "-c", "pass")
    run(tmp_path, "run", "--", sys.executable, "-c", "pass")
    assert "jobs run: 3" in run(tmp_path, "report", "--resource", "ram").stdout  # GPU jobs hold RAM too
    assert "jobs run: 2" in run(tmp_path, "report").stdout


def test_old_events_without_a_resource_count_as_gpu(tmp_path):
    import datetime
    ts = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    (tmp_path / "events.jsonl").write_text(
        json.dumps({"ts": ts, "event": "end", "cwd": "x", "seconds": 3600, "exit_code": 0}) + "\n")
    assert "jobs run: 1" in run(tmp_path, "report").stdout
    assert "jobs run: 0" in run(tmp_path, "report", "--resource", "ram").stdout


def test_ram_hold_takes_only_the_ram_lock(tmp_path):
    r = run(tmp_path, "hold", "--resource", "ram", "--", sys.executable, "-c", "pass")
    assert r.returncode == 0
    assert {e["resource"] for e in events(tmp_path) if e["event"] == "start"} == {"ram"}


def test_low_memory_refuses_without_wait_and_holds_nothing(tmp_path):
    r = run(tmp_path, "run", "--purpose", "big", "--", sys.executable, "-c", "pass",
            extra_env={"GPU_RUN_MIN_FREE_GB": "100000"})
    assert r.returncode == 3 and "of memory is free" in r.stderr
    ev = events(tmp_path)
    assert [e["event"] for e in ev] == ["refused"] and ev[0]["reason"] == "low_memory"
    assert "RAM lock is free" in run(tmp_path, "status", "--resource", "ram").stdout
    assert "held back for low memory (waited or refused): 1" in run(tmp_path, "report", "--resource", "ram").stdout


def test_low_memory_waits_with_wait_until_memory_frees(tmp_path, monkeypatch):
    import argparse
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(g, "POLL_SECONDS", 0)
    readings = iter([1.0, 2.0, 9.0])
    monkeypatch.setattr(g, "mem_free_gb", lambda: next(readings, 9.0))
    monkeypatch.setattr(g, "mem_phys_free_gb", lambda: 9.0)
    args = argparse.Namespace(command=[sys.executable, "-c", "pass"], purpose="job", wait=True,
                              keep_ollama=True, resource="ram", min_free_gb=4.0)
    assert g.cmd_run(args) == 0
    ev = events(tmp_path)
    assert [e["event"] for e in ev] == ["waiting", "start", "end"]
    assert ev[0]["reason"] == "low_memory" and ev[1]["mem_free_gb"] == 9.0


def test_admission_uses_the_lower_of_commit_and_physical(monkeypatch, tmp_path):
    import argparse
    g = _module()
    monkeypatch.setattr(g, "mem_free_gb", lambda: 9.0)
    monkeypatch.setattr(g, "mem_phys_free_gb", lambda: 1.5)
    args = argparse.Namespace(wait=False, min_free_gb=4.0)
    info = {"resource": "ram", "purpose": "p", "cmd": "c", "cwd": "d"}
    assert g._admit(args, info) is False
    assert info["mem_free_gb"] == 9.0 and info["mem_phys_free_gb"] == 1.5
    monkeypatch.setattr(g, "mem_phys_free_gb", lambda: 8.0)
    assert g._admit(args, info) is True


def test_top_memory_names_the_biggest_programs(monkeypatch):
    g = _module()
    fake = "\n".join(['"a.exe","1","Console","1","3,000 K"', '"b.exe","2","Console","1","9,000 K"',
                      '"a.exe","3","Console","1","4,000 K"'])
    monkeypatch.setattr(g.sys, "platform", "win32")
    monkeypatch.setattr(g.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, fake, ""))
    assert g.top_memory(2) == {"b.exe": 9, "a.exe": 7}


def test_top_memory_live_reads_something():
    top = _module().top_memory(3)
    assert top is None or (len(top) == 3 and all(v >= 0 for v in top.values()))


def test_mem_phys_free_reads_a_positive_figure():
    assert _module().mem_phys_free_gb() > 0


def test_mem_free_reads_a_positive_figure():
    free = _module().mem_free_gb()
    assert free is None or free > 0


def test_a_holder_that_died_is_logged_as_lost(tmp_path, monkeypatch):
    import os
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    dead = g.Lock("gpu")
    assert dead.try_acquire({"pid": 999999, "purpose": "killed"})
    os.close(dead.fd)  # dies without release(): the OS frees the lock, the record stays
    dead.fd = None
    assert run(tmp_path, "run", "--", sys.executable, "-c", "pass").returncode == 0
    lost = [e for e in events(tmp_path) if e["event"] == "lost"]
    assert len(lost) == 1 and lost[0]["held_by"]["purpose"] == "killed"
    run(tmp_path, "run", "--", sys.executable, "-c", "pass")  # a clean release leaves no record
    assert len([e for e in events(tmp_path) if e["event"] == "lost"]) == 1
    assert "lost holders (wrapper died without releasing; job may have been killed): 1" in \
        run(tmp_path, "report").stdout


def test_killing_the_wrapper_kills_its_job(tmp_path):
    import time
    if sys.platform != "win32":
        return
    marker = tmp_path / "child.pid"
    code = f"import os,time;open(r'{marker}','w').write(str(os.getpid()));time.sleep(60)"
    wrapper = subprocess.Popen([sys.executable, SCRIPT, "run", "--resource", "ram", "--", sys.executable, "-c", code],
                               env=ENV(tmp_path))
    for _ in range(80):
        if marker.exists() and marker.read_text():
            break
        time.sleep(0.25)
    child = int(marker.read_text())
    subprocess.run(["taskkill", "/F", "/PID", str(wrapper.pid)], capture_output=True)  # the wrapper only, no /T
    wrapper.wait()
    time.sleep(1)
    alive = subprocess.run(["tasklist", "/FI", f"PID eq {child}", "/NH"], capture_output=True, text=True).stdout
    assert str(child) not in alive


def test_thermal_report_counts_time_at_limits_trigger_and_slowdown(tmp_path):
    import datetime
    t0 = datetime.datetime.now().astimezone()
    lines = [{"ts": t0.isoformat(timespec="seconds"), "event": "start", "interval_s": 60,
              "limits": {"target_c": 87.0, "slowdown_c": 95.0, "shutdown_c": 100.0}}]
    # temps 70, 88, 96, 90; counters 0 -> 0 -> 30 s -> reboot (reset to 5 s, not counted) -> 15 s
    for i, (temp, us) in enumerate([(70, 0), (88, 0), (96, 30e6), (90, 5e6), (89, 15e6)]):
        ts = (t0 + datetime.timedelta(seconds=60 * (i + 1))).isoformat(timespec="seconds")
        lines.append({"ts": ts, "event": "sample", "gpu_temp_c": temp, "power_w": 60 + i,
                      "thermal_slowdown": temp >= 95, "slowdown_us": us, "cpu_temp_c": None})
    (tmp_path / "thermal.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines))
    out = run(tmp_path, "report", "--thermal", "--days", "1").stdout
    assert "GPU peak 96 C" in out and "peak power 64 W" in out
    assert "at or above target (87.0 C): 4 min" in out
    assert "at or above slowdown (95.0 C): 1 min" in out
    assert "thermal slowdown: 40 s by the counters, 1 samples with it active" in out
    assert "trigger 87 C (what a pause rule would act on): 4" in out
    assert "trigger 90 C (what a pause rule would act on): 2" in run(
        tmp_path, "report", "--thermal", "--days", "1", "--trigger-c", "90").stdout


def test_thermal_report_counts_cpu_time_hot_and_clock_under_load(tmp_path):
    import datetime
    t0 = datetime.datetime.now().astimezone()
    lines = [{"ts": t0.isoformat(timespec="seconds"), "event": "start", "interval_s": 60, "limits": {}}]
    # (temp, MHz, load): idle sample ignored for the clock; 3 min at >= 90, 2 within 5 C of TjMax 100
    for i, (temp, mhz, load) in enumerate([(60, 800, 5), (85, 4000, 95), (92, 3900, 95),
                                           (96, 3000, 100), (97, 2600, 100)]):
        ts = (t0 + datetime.timedelta(seconds=60 * (i + 1))).isoformat(timespec="seconds")
        lines.append({"ts": ts, "event": "sample", "gpu_temp_c": 60, "cpu_temp_c": temp, "cpu_mhz": mhz,
                      "cpu_load_pct": load, "cpu_tjmax_c": 100})
    (tmp_path / "thermal.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines))
    out = run(tmp_path, "report", "--thermal", "--days", "1").stdout
    assert "CPU package: peak 97 C" in out
    assert "at or above 90 C: 3 min" in out and "within 5 C of TjMax (100 C): 2 min" in out
    assert "CPU clock under load (>= 80%, 4 samples): median 3900 MHz" in out and "min 2600 MHz" in out
    assert "at or above 95 C: 2 min" in run(
        tmp_path, "report", "--thermal", "--days", "1", "--cpu-threshold-c", "95").stdout


def test_thermal_report_with_no_log_says_how_to_start(tmp_path):
    out = run(tmp_path, "report", "--thermal").stdout
    assert "no samples" in out


def test_gpu_limits_parses_nvidia_smi_query(monkeypatch):
    sys.path.insert(0, str(HERE))
    import gpu_run

    text = ("    Temperature\n        GPU Current Temp                  : 50 C\n"
            "        GPU Shutdown Temp                 : 100 C\n        GPU Slowdown Temp : 95 C\n"
            "        GPU Max Operating Temp            : 102 C\n"
            "        GPU Target Temperature Specification : 87 C\n        Memory Max Operating Temp : N/A\n")
    monkeypatch.setattr(gpu_run.subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout=text, stderr=""))
    assert gpu_run.gpu_limits() == {"shutdown_c": 100.0, "slowdown_c": 95.0,
                                    "max_operating_c": 102.0, "target_c": 87.0}


def test_thermal_report_uses_the_interval_of_a_logger_started_before_since(tmp_path):
    import datetime
    t0 = datetime.datetime.now().astimezone().replace(microsecond=0)
    lines = [{"ts": t0.isoformat(), "event": "start", "interval_s": 15, "limits": {"target_c": 87.0}}]
    for i in range(8):  # 8 samples of 15 s at 90 C = 2 min, all after --since
        lines.append({"ts": (t0 + datetime.timedelta(seconds=60 + 15 * i)).isoformat(), "event": "sample",
                      "gpu_temp_c": 90, "slowdown_us": 0})
    (tmp_path / "thermal.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines))
    since = (t0 + datetime.timedelta(seconds=30)).isoformat()
    out = run(tmp_path, "report", "--thermal", "--since", since).stdout
    assert "samples: 8 (0.0 h logged)" in out
    assert "at or above target (87.0 C): 2 min" in out


def test_check_flags_a_clock_cap_left_on_with_no_lock(tmp_path, monkeypatch, capsys):
    sys.path.insert(0, str(HERE))
    import gpu_run

    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(gpu_run, "gpu_reading", lambda: None)
    monkeypatch.setattr(gpu_run, "boot_time", lambda: 0.0)
    assert gpu_run.clock_cap_left_on() is None  # no marker: no cap
    (tmp_path / "clock-cap").write_text("on")
    assert gpu_run.cmd_check(None) == 0
    assert "CLOCK CAP left on" in capsys.readouterr().out
    assert any(e["event"] == "clock_cap_left_on" for e in events(tmp_path))
    monkeypatch.setattr(gpu_run, "boot_time", lambda: 9e12)  # marker older than the boot: stale
    assert gpu_run.clock_cap_left_on() is None


def test_clock_cap_is_not_flagged_while_a_lock_is_held(tmp_path, monkeypatch):
    sys.path.insert(0, str(HERE))
    import gpu_run

    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(gpu_run, "boot_time", lambda: 0.0)
    (tmp_path / "clock-cap").write_text("on")
    monkeypatch.setattr(gpu_run.Lock, "is_held", lambda self: True)
    assert gpu_run.clock_cap_left_on() is None


def test_rotate_months_moves_old_lines_and_readers_see_both(tmp_path):
    from datetime import datetime, timedelta
    sys.path.insert(0, str(HERE))
    import guard_logs
    now = datetime.now().astimezone()
    old = (now.replace(day=1) - timedelta(days=3)).replace(microsecond=0)
    rows = [{"ts": old.isoformat(), "event": "sample", "n": 1}, {"ts": now.isoformat(), "event": "sample", "n": 2}]
    (tmp_path / "thermal.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows))
    assert guard_logs.rotate_months(tmp_path) == 1
    assert guard_logs.rotate_months(tmp_path) == 0  # nothing left to move
    archive = tmp_path / f"thermal-{old.strftime('%Y-%m')}.jsonl"
    assert json.loads(archive.read_text())["n"] == 1
    assert [json.loads(x)["n"] for x in (tmp_path / "thermal.jsonl").read_text().splitlines()] == [2]
    assert [r["n"] for r in guard_logs.read_rows(tmp_path, "thermal.jsonl", old - timedelta(days=1))] == [1, 2]
    assert [r["n"] for r in guard_logs.read_rows(tmp_path, "thermal.jsonl", now - timedelta(minutes=1))] == [2]
    (tmp_path / "big.jsonl").write_bytes(b"x" * (guard_logs.WARN_BYTES + 1))
    assert any("WARNING" in line and "big.jsonl" in line for line in guard_logs.size_report(tmp_path))


def test_cap_on_and_off_start_the_task_and_report_the_marker(tmp_path, monkeypatch, capsys):
    sys.path.insert(0, str(HERE))
    import gpu_run

    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(gpu_run, "CAP_WAIT_SECONDS", 1)
    started = []

    def fake_run(cmd, **kw):  # the elevated task writes or removes the marker
        started.append(cmd[-1])
        m = tmp_path / "clock-cap"
        m.write_text("on") if cmd[-1].endswith("-on") else m.unlink(missing_ok=True)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(gpu_run.subprocess, "run", fake_run)
    assert gpu_run.main(["cap", "on"]) == 0 and "ON" in capsys.readouterr().out
    assert gpu_run.main(["cap", "status"]) == 0 and "ON" in capsys.readouterr().out
    assert gpu_run.main(["cap", "off"]) == 0 and "OFF" in capsys.readouterr().out
    assert started == ["gpu-clock-cap-on", "gpu-clock-cap-off"]


def test_cap_reports_failure_when_the_task_does_not_change_the_marker(tmp_path, monkeypatch, capsys):
    sys.path.insert(0, str(HERE))
    import gpu_run

    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(gpu_run, "CAP_WAIT_SECONDS", 1)
    monkeypatch.setattr(gpu_run.subprocess, "run", lambda c, **k: subprocess.CompletedProcess(c, 0, stdout="", stderr=""))
    assert gpu_run.main(["cap", "on"]) == 1


def test_thermal_watch_warns_after_sustained_heat_stops_near_slowdown_and_resets():
    import gpu_run as g
    w = g.ThermalWatch({"target_c": 87, "slowdown_c": 95}, warn_s=300, stop_s=120)
    assert (w.warn_c, w.stop_c) == (80, 92)
    assert w.update(0, 70) is None
    assert w.update(10, 81) is None  # hot, the clock starts
    assert w.update(200, 81) is None
    assert w.update(250, 79) is None  # a cool reading resets the clock
    assert w.update(260, 81) is None
    assert w.update(500, 81) is None
    assert w.update(570, 81) == "warn"  # 310 s since 260
    assert w.update(600, 81) is None  # only once
    assert w.update(700, 93) is None
    assert w.update(830, 93) == "stop"  # 130 s at or above 92


def test_thermal_watch_warns_when_the_slowdown_counter_rises_and_defaults_without_limits():
    import gpu_run as g
    w = g.ThermalWatch()
    assert (w.warn_c, w.stop_c) == (80.0, 92.0)
    assert w.update(0, 60, 1000) is None
    assert w.update(15, 60, 1000) is None
    assert w.update(30, 60, 2500) == "warn"
    assert g.ThermalWatch().update(0, None) is None


def test_hold_stops_a_gpu_service_that_stays_too_hot(tmp_path, monkeypatch):
    import argparse
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(g, "HOLD_POLL_SECONDS", 0)
    monkeypatch.setattr(g, "WATCH_SECONDS", 0)
    monkeypatch.setattr(g, "ollama_models", lambda: [])
    monkeypatch.setattr(g, "gpu_limits", lambda: {"target_c": 87, "slowdown_c": 95})
    monkeypatch.setattr(g, "thermal_reading", lambda: {"gpu_temp_c": 93.0, "slowdown_us": None, "thermal_slowdown": False})
    clock = iter(range(0, 10000, 70))  # each watch step is 70 s later: the second step reaches STOP_S
    monkeypatch.setattr(g.time, "time", lambda: 1e9 + next(clock))
    calls = iter([{}])
    monkeypatch.setattr(g, "containers", lambda gpu_only=True: next(calls, {"new": "rr"}))
    monkeypatch.setattr(g, "containers_mem_mb", lambda ids: 0.0)
    stopped = []
    monkeypatch.setattr(g, "stop_containers", lambda ids: stopped.append(ids) or True)
    args = argparse.Namespace(command=[sys.executable, "-c", "pass"], purpose="svc", wait=False, keep_ollama=False)
    assert g.cmd_hold(args) == 4
    assert stopped == [["new"]]
    names = [e["event"] for e in events(tmp_path)]
    assert "thermal_stop" in names and "thermal_stopped" in names
    assert not g.Lock().is_held()


def test_ram_hold_does_not_watch_the_gpu(tmp_path, monkeypatch):
    import argparse
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(g, "HOLD_POLL_SECONDS", 0)
    monkeypatch.setattr(g, "WATCH_SECONDS", 0)
    monkeypatch.setattr(g, "ollama_models", lambda: [])
    monkeypatch.setattr(g, "thermal_reading", lambda: pytest.fail("RAM hold read the GPU"))
    calls = iter([{}, {"new": "rr"}, {}])
    monkeypatch.setattr(g, "containers", lambda gpu_only=True: next(calls))
    monkeypatch.setattr(g, "containers_mem_mb", lambda ids: 0.0)
    args = argparse.Namespace(command=[sys.executable, "-c", "pass"], purpose="svc", wait=False,
                              keep_ollama=False, resource="ram")
    assert g.cmd_hold(args) == 0
