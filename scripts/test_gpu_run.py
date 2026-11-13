import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCRIPT = str(HERE / "gpu_run.py")


def run(tmp, *args, **kw):
    env = {**__import__("os").environ, "GPU_GUARD_DIR": str(tmp), "OLLAMA_HOST": "127.0.0.1:1"}
    return subprocess.run([sys.executable, SCRIPT, *args], env=env, capture_output=True, text=True, **kw)


def events(tmp):
    return [json.loads(x) for x in (tmp / "events.jsonl").read_text().splitlines()]


def test_runs_command_logs_and_forwards_exit_code(tmp_path):
    r = run(tmp_path, "run", "--purpose", "t", "--", sys.executable, "-c", "raise SystemExit(7)")
    assert r.returncode == 7
    assert [e["event"] for e in events(tmp_path)] == ["start", "end"]
    assert events(tmp_path)[1]["exit_code"] == 7


def test_child_sees_held_by_and_lock_is_free_after(tmp_path):
    code = "import os;print(os.environ['GPU_GUARD_HELD_BY'])"
    r = run(tmp_path, "run", "--", sys.executable, "-c", code)
    assert r.stdout.strip().isdigit()
    assert "free" in run(tmp_path, "status").stdout


def test_second_job_is_refused_and_logged(tmp_path):
    holder = subprocess.Popen(
        [sys.executable, SCRIPT, "run", "--purpose", "first", "--", sys.executable, "-c",
         "import time;time.sleep(6)"],
        env={**__import__("os").environ, "GPU_GUARD_DIR": str(tmp_path), "OLLAMA_HOST": "127.0.0.1:1"},
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
        assert "refused (GPU taken, did not wait): 1" in run(tmp_path, "report").stdout
    finally:
        holder.wait()


def _module():
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


def test_hold_keeps_lock_until_its_containers_stop(tmp_path, monkeypatch):
    import argparse
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(g, "HOLD_POLL_SECONDS", 0)
    monkeypatch.setattr(g, "ollama_models", lambda: [])
    seen = {"status_while_held": None}
    calls = iter([{"old": "other"}, {"old": "other", "new": "rr"}, {"old": "other", "new": "rr"}, {"old": "other"}])

    def fake_containers():
        c = next(calls)
        if c == {"old": "other", "new": "rr"} and seen["status_while_held"] is None:
            seen["status_while_held"] = g.Lock().is_held()
        return c

    monkeypatch.setattr(g, "gpu_containers", fake_containers)
    args = argparse.Namespace(command=["--", sys.executable, "-c", "pass"], purpose="svc", wait=False,
                              keep_ollama=False)
    assert g.cmd_hold(args) == 0
    assert seen["status_while_held"] is True
    assert not g.Lock().is_held()
    ev = events(tmp_path)
    assert [e["event"] for e in ev] == ["start", "hold", "end"]
    assert ev[1]["containers"] == ["rr"] and ev[2]["kind"] == "service"


def test_hold_releases_when_no_new_gpu_container(tmp_path, monkeypatch):
    import argparse
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(g, "ollama_models", lambda: [])
    monkeypatch.setattr(g, "gpu_containers", lambda: {"old": "other"})
    args = argparse.Namespace(command=[sys.executable, "-c", "pass"], purpose="svc", wait=False,
                              keep_ollama=False)
    assert g.cmd_hold(args) == 0
    assert [e["event"] for e in events(tmp_path)] == ["start", "end"]
    assert not g.Lock().is_held()


def test_hold_stops_containers_at_the_deadline(tmp_path, monkeypatch):
    import argparse
    g = _module()
    monkeypatch.setenv("GPU_GUARD_DIR", str(tmp_path))
    monkeypatch.setattr(g, "HOLD_POLL_SECONDS", 0)
    monkeypatch.setattr(g, "ollama_models", lambda: [])
    state = {"n": 0, "stopped": None}

    def fake_containers():
        state["n"] += 1
        return {} if state["n"] == 1 else {"new": "rr"}

    def fake_stop(ids):
        state["stopped"] = ids
        return True

    monkeypatch.setattr(g, "gpu_containers", fake_containers)
    monkeypatch.setattr(g, "stop_containers", fake_stop)
    args = argparse.Namespace(command=[sys.executable, "-c", "pass"], purpose="svc", wait=False,
                              keep_ollama=False, max_minutes=1e-9)
    assert g.cmd_hold(args) == 124
    assert state["stopped"] == ["new"]
    assert [e["event"] for e in events(tmp_path)] == ["start", "hold", "deadline", "end"]
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
    ev = events(tmp_path)
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
    assert [e["event"] for e in events(tmp_path)] == ["start", "end"]


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
    assert events(tmp_path)[1]["ok"] is False


def test_old_stop_ollama_flag_is_still_accepted(tmp_path):
    r = run(tmp_path, "run", "--stop-ollama", "--", sys.executable, "-c", "pass")
    assert r.returncode == 0


def test_ram_lock_is_separate_from_the_gpu_lock(tmp_path):
    import time
    holder = subprocess.Popen(
        [sys.executable, SCRIPT, "run", "--resource", "ram", "--purpose", "suite", "--", sys.executable, "-c",
         "import time;time.sleep(6)"],
        env={**__import__("os").environ, "GPU_GUARD_DIR": str(tmp_path), "OLLAMA_HOST": "127.0.0.1:1"},
    )
    try:
        for _ in range(40):
            if "held" in run(tmp_path, "status", "--resource", "ram").stdout:
                break
            time.sleep(0.25)
        assert "RAM held by suite" in run(tmp_path, "status", "--resource", "ram").stdout
        assert "free" in run(tmp_path, "status").stdout  # the GPU lock is untouched
        gpu = run(tmp_path, "run", "--", sys.executable, "-c", "pass")
        assert gpu.returncode == 0
        second = run(tmp_path, "run", "--resource", "ram", "--purpose", "build", "--", sys.executable, "-c", "pass")
        assert second.returncode == 3 and "RAM/CPU lock is in use by suite" in second.stderr
        out = run(tmp_path, "report", "--resource", "ram").stdout
        assert "refused (lock taken, did not wait): 1" in out
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
    assert "jobs run: 1" in run(tmp_path, "report", "--resource", "ram").stdout
    assert "jobs run: 2" in run(tmp_path, "report").stdout


def test_old_events_without_a_resource_count_as_gpu(tmp_path):
    import datetime
    ts = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    (tmp_path / "events.jsonl").write_text(
        json.dumps({"ts": ts, "event": "end", "cwd": "x", "seconds": 3600, "exit_code": 0}) + "\n")
    assert "jobs run: 1" in run(tmp_path, "report").stdout
    assert "jobs run: 0" in run(tmp_path, "report", "--resource", "ram").stdout


def test_hold_does_not_take_a_resource_option(tmp_path):
    assert run(tmp_path, "hold", "--resource", "ram", "--", sys.executable, "-c", "pass").returncode == 2
