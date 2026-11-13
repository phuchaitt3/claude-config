import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("gpu_watch", Path(__file__).with_name("gpu_watch.py"))
assert _spec and _spec.loader
gpu_watch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gpu_watch)

BUSY = {"util_pct": 90.0, "mem_mb": 4000.0}


def test_silent_when_idle_locked_or_unreadable():
    for reading, locked, busy in ((BUSY, True, True), (BUSY, False, False), (None, False, False)):
        _, text, log = gpu_watch.decide({}, 1000.0, reading, locked, busy)
        assert text == "" and not log


def test_unguarded_use_is_logged_and_told_once_per_window():
    state, text, log = gpu_watch.decide({}, 1000.0, BUSY, False, True)
    assert log and "outside `gpu_run.py`" in text
    _, text2, log2 = gpu_watch.decide(state, 1200.0, BUSY, False, True)
    assert not log2 and text2 == ""
    _, text3, log3 = gpu_watch.decide(state, 1000.0 + gpu_watch.LOG_EVERY_S, BUSY, False, True)
    assert log3 and text3


def test_ollama_memory_is_named_not_called_unguarded():
    models = [{"name": "qwen3:4b", "vram_mb": 3900}]
    _, text, log = gpu_watch.decide({}, 1000.0, BUSY, False, True, models)
    assert log and "qwen3:4b" in text and "unloads them" in text
    _, text, _ = gpu_watch.decide({}, 1000.0, BUSY, False, True, [{"name": "s", "vram_mb": 500}])
    assert "outside `gpu_run.py`" in text
