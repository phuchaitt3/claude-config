import importlib.util, json
from pathlib import Path

_spec = importlib.util.spec_from_file_location("selfdrive_run", Path(__file__).with_name("selfdrive_run.py"))
run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run)


def chat(root, folder, sid, prompt, ts, out=100, last=None):
    d = root / folder
    d.mkdir(parents=True, exist_ok=True)
    rows = [
        {"timestamp": ts, "message": {"role": "user", "content": prompt}},
        {"timestamp": ts, "message": {"id": "m" + sid, "model": "x", "role": "assistant",
                                      "usage": {"input_tokens": 0, "output_tokens": out}}},
    ]
    if last:
        rows.append({"timestamp": last, "message": {"id": "z" + sid, "model": "x", "role": "assistant",
                                                    "usage": {"input_tokens": 0, "output_tokens": 1}}})
    (d / (sid + ".jsonl")).write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


def test_runs_group_loops_workers_and_keep_repos_apart(tmp_path):
    loop = "Self-drive overnight in book-rag-app (main checkout, branch main)."
    chat(tmp_path, "x-book-rag-app-main", "L1", loop, "2026-11-23T17:00:00Z", last="2026-11-23T20:00:00Z")
    chat(tmp_path, "x-book-rag-app-main", "L2", loop, "2026-11-23T21:00:00Z")          # successor
    chat(tmp_path, "x-book-rag-app-main", "W1", "Work GitHub issue #7 in o/book-rag-app", "2026-11-23T18:00:00Z")
    chat(tmp_path, "x-book-rag-app-main", "N1", "just chatting about cost", "2026-11-23T19:00:00Z")   # not a worker
    chat(tmp_path, "x-thesis-main", "T1", "Self-drive overnight in thesis (main checkout)", "2026-11-23T17:30:00Z", last="2026-11-23T23:00:00Z")
    chat(tmp_path, "x-thesis-main", "T2", "Work GitHub issue #9", "2026-11-23T18:30:00Z")
    runs = run.group_runs("book-rag-app", run.repo_chats("book-rag-app", str(tmp_path)))
    assert len(runs) == 1
    assert [c[1] for c in runs[0]["loops"]] == ["L1", "L2"]
    assert [c[1] for c in runs[0]["workers"]] == ["W1"]
    other = run.group_runs("thesis", run.repo_chats("thesis", str(tmp_path)))
    assert [c[1] for c in other[0]["workers"]] == ["T2"]


def test_a_gap_over_the_limit_starts_a_new_run(tmp_path):
    loop = "Self-drive overnight in app"
    chat(tmp_path, "x-app-main", "A", loop, "2026-11-20T01:00:00Z")
    chat(tmp_path, "x-app-main", "B", loop, "2026-11-22T01:00:00Z")
    assert len(run.group_runs("app", run.repo_chats("app", str(tmp_path)))) == 2


def test_foreign_tokens_exclude_the_run_and_net_rise_ignores_noise(tmp_path):
    chat(tmp_path, "x-app-main", "A", "Self-drive overnight in app", "2026-11-20T01:00:00Z", out=100)
    chat(tmp_path, "y-other", "Z", "something else", "2026-11-20T01:00:00Z", out=200)
    t0 = run._epoch("2026-11-20T00:00:00Z"); t1 = run._epoch("2026-11-20T02:00:00Z")
    assert run.foreign_weighted(t0, t1, {"A"}, str(tmp_path)) == 1000.0   # 200 output x5
    log = tmp_path / "q.jsonl"
    rows = [dict(t=t0 - 60, week=10.0, week_resets=9e9), dict(t=t0 + 60, week=14.0, week_resets=9e9),
            dict(t=t0 + 120, week=9.0, week_resets=9e9), dict(t=t0 + 180, week=13.0, week_resets=9e9)]
    log.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    assert run.net_rise(str(log), "2026-11-20T00:00:00Z", "2026-11-20T02:00:00Z") == 4.0   # the 9 and the 13 are lower than the 14 in one window: stale, dropped
