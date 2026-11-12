import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCRIPT = str(HERE / "gpu_run.py")


def run(tmp, *args, **kw):
    env = {**__import__("os").environ, "GPU_GUARD_DIR": str(tmp)}
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
        env={**__import__("os").environ, "GPU_GUARD_DIR": str(tmp_path)},
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
