import importlib.util
import json
import os
from datetime import datetime
from pathlib import Path

_spec = importlib.util.spec_from_file_location("loop_watch", Path(__file__).with_name("loop_watch.py"))
assert _spec and _spec.loader
lw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lw)

FOLDER = "d:\\1.git_projs\\proj\\main"
SLUG = "d--1-git-projs-proj-main"
NOW = "2026-11-14T12:00:00+00:00"
NOW_EPOCH = datetime.fromisoformat(NOW).timestamp()


def user(ts, text, sid):
    return {"type": "user", "timestamp": ts, "sessionId": sid,
            "message": {"role": "user", "content": [{"type": "text", "text": text}]}}


def wake(ts, sid, **inp):
    return {"type": "assistant", "timestamp": ts, "sessionId": sid, "message": {
        "role": "assistant", "content": [{"type": "tool_use", "name": "ScheduleWakeup", "input": inp}]}}


def write(root, name, entries, age_min):
    d = root / SLUG
    d.mkdir(exist_ok=True)
    p = d / f"{name}.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")
    t = NOW_EPOCH - age_min * 60
    os.utime(p, (t, t))


def run(root, capsys):
    lw.main([FOLDER, "--projects-dir", str(root), "--now", NOW])
    return capsys.readouterr().out


def live(sid, name, start, wake_ts=None, **inp):
    e = [{"type": "agent-name", "agentName": name, "sessionId": sid},
         user(start, "# /loop - schedule", sid)]
    if wake_ts:
        e.append(wake(wake_ts, sid, **inp))
    return e


def test_waiting_when_a_wakeup_is_pending(tmp_path, capsys):
    write(tmp_path, "a", live("aaa", "loop-a", "2026-11-14T11:00:00Z", "2026-11-14T11:50:00Z", delaySeconds=1200), 10)
    out = run(tmp_path, capsys)
    assert "aaa loop-a" in out and "wakeup 1200s" in out and out.strip().endswith("WAITING")


def test_stalled_when_last_turn_is_old_and_no_wakeup(tmp_path, capsys):
    e = live("bbb", "loop-b", "2026-11-14T10:00:00Z", "2026-11-14T10:05:00Z", delaySeconds=600)
    e.append(user("2026-11-14T10:20:00Z", "wake", "bbb"))  # woke, then no new wakeup
    write(tmp_path, "b", e, 100)
    assert run(tmp_path, capsys).strip().endswith("STALLED")


def test_recent_turn_without_wakeup_is_running(tmp_path, capsys):
    write(tmp_path, "c", live("ccc", "loop-c", "2026-11-14T11:50:00Z"), 5)
    assert run(tmp_path, capsys).strip().endswith("RUNNING")


def test_stopped_loop_is_no_loop(tmp_path, capsys):
    e = live("ddd", "loop-d", "2026-11-14T11:00:00Z", "2026-11-14T11:30:00Z", stop=True)
    write(tmp_path, "d", e, 20)
    assert run(tmp_path, capsys).strip() == f"{FOLDER}: NO LOOP"


def test_replaced_chat_reports_the_new_loop_not_the_finished_one(tmp_path, capsys):
    old = live("oldsession", "old-chat", "2026-11-14T08:00:00Z", "2026-11-14T09:00:00Z", stop=True)
    new = live("newsession", "new-chat", "2026-11-14T11:00:00Z", "2026-11-14T11:40:00Z", delaySeconds=1800)
    write(tmp_path, "old", old, 180)
    write(tmp_path, "new", new, 20)
    out = run(tmp_path, capsys)
    assert "newsession new-chat" in out and "oldsession" not in out


def test_two_chats_in_one_folder_newer_plain_chat_does_not_hide_the_loop(tmp_path, capsys):
    plain = [user("2026-11-14T11:55:00Z", "hello", "plain")]
    loop = live("lll", "loop-l", "2026-11-14T10:00:00Z", "2026-11-14T11:30:00Z", delaySeconds=1800)
    write(tmp_path, "plain", plain, 5)
    write(tmp_path, "loop", loop, 30)
    assert "lll loop-l" in run(tmp_path, capsys)


def test_ancient_live_loop_is_ignored(tmp_path, capsys):
    write(tmp_path, "z", live("zzz", "dead", "2026-11-10T11:00:00Z", "2026-11-10T11:30:00Z", delaySeconds=600), 60 * 24 * 4)
    assert run(tmp_path, capsys).strip().endswith("NO LOOP")


def test_tool_results_do_not_clear_a_pending_wakeup(tmp_path, capsys):
    e = live("eee", "loop-e", "2026-11-14T11:00:00Z", "2026-11-14T11:50:00Z", delaySeconds=900)
    e.append({"type": "user", "timestamp": "2026-11-14T11:50:01Z", "sessionId": "eee",
              "message": {"content": [{"type": "tool_result", "content": "ok"}]}})
    write(tmp_path, "e", e, 10)
    assert run(tmp_path, capsys).strip().endswith("WAITING")


def test_human_peer_and_task_messages_leave_the_wakeup_pending(tmp_path, capsys):
    e = live("fff", "loop-f", "2026-11-14T11:00:00Z", "2026-11-14T11:50:00Z", delaySeconds=1200)
    for kind in ("human", "peer", "task-notification"):
        m = user("2026-11-14T11:52:00Z", "hi", "fff")
        m["origin"] = {"kind": kind}
        e.append(m)
    write(tmp_path, "f", e, 8)
    assert run(tmp_path, capsys).strip().endswith("WAITING")


def test_local_slash_command_leaves_the_wakeup_pending(tmp_path, capsys):
    e = live("ggg", "loop-g", "2026-11-14T11:00:00Z", "2026-11-14T11:50:00Z", delaySeconds=1200)
    e.append(user("2026-11-14T11:52:00Z", "<command-name>/reload-plugins</command-name>", "ggg"))
    write(tmp_path, "g", e, 8)
    assert run(tmp_path, capsys).strip().endswith("WAITING")


def test_system_reminder_leaves_the_wakeup_pending(tmp_path, capsys):
    e = live("hhh", "loop-h", "2026-11-14T11:00:00Z", "2026-11-14T11:50:00Z", delaySeconds=1200)
    e.append(user("2026-11-14T11:52:00Z", "<system-reminder>note</system-reminder>", "hhh"))
    write(tmp_path, "h", e, 8)
    assert run(tmp_path, capsys).strip().endswith("WAITING")


def test_missing_folder_is_no_loop(tmp_path, capsys):
    assert run(tmp_path, capsys).strip().endswith("NO LOOP")
