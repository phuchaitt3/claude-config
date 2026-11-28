import json

import pytest

import kaggle_slots as ks


class Fake:
    """`rounds` is a list of {version: state}; each check of the kernel uses the next one."""

    def __init__(self, rounds, sources=None, error=None):
        self.rounds, self.sources, self.error = list(rounds), sources or {}, error
        self.current = {}

    def latest_version(self, ref):
        if self.error:
            raise self.error
        self.current = self.rounds.pop(0) if len(self.rounds) > 1 else self.rounds[0]
        return max(self.current, default=0)

    def state(self, ref, version):
        return self.current.get(version, "COMPLETE")

    def source(self, ref, version):
        return self.sources.get(version, "old code")

    def recent(self):
        return ["me/a"], 1


def run(tmp_path, fake, *flags, replies=("pushed",)):
    (tmp_path / "kernel-metadata.json").write_text(
        json.dumps({"id": "me/a", "code_file": "s.py"}), encoding="utf-8"
    )
    (tmp_path / "s.py").write_text("new code\n", encoding="utf-8")
    sent, slept, queue = [], [], list(replies)

    def send(command):
        sent.append(command)
        return 0, queue.pop(0)

    args = ks.parser().parse_args(["push", "-p", str(tmp_path), *flags])
    ks.push(fake, args, send=send, sleep=slept.append, clock=lambda: 0.0)
    return sent, slept


def test_pushes_at_once_when_nothing_is_active(tmp_path):
    sent, slept = run(tmp_path, Fake([{}]), "--accelerator", "T4", "--run-timeout", "60")
    assert sent == [["kaggle", "kernels", "push", "-p", str(tmp_path),
                     "--accelerator", "T4", "-t", "60"]]  # fmt: skip
    assert slept == []


def test_waits_while_an_older_version_runs_behind_a_cancelled_one(tmp_path):
    busy = {2: "RUNNING", 3: "CANCEL_ACKNOWLEDGED"}
    sent, slept = run(tmp_path, Fake([busy, busy, {3: "COMPLETE"}]))
    assert len(sent) == 1 and len(slept) == 2


def test_refuses_code_identical_to_an_active_version(tmp_path):
    fake = Fake([{2: "RUNNING"}], sources={2: "new code\r\n"})
    with pytest.raises(SystemExit, match="identical code"):
        run(tmp_path, fake)


def test_no_wait_exits_on_an_active_version(tmp_path):
    with pytest.raises(SystemExit, match="nothing was pushed"):
        run(tmp_path, Fake([{1: "QUEUED"}]), "--no-wait")


def test_allow_active_skips_the_check(tmp_path):
    sent, _ = run(tmp_path, Fake([{1: "RUNNING"}], error=OSError("down")), "--allow-active")
    assert len(sent) == 1


def test_unreadable_state_pushes_nothing(tmp_path):
    with pytest.raises(SystemExit, match="could not check"):
        run(tmp_path, Fake([{}], error=OSError("down")))


def test_retries_while_both_sessions_are_taken(tmp_path):
    full = "Kernel push error: Maximum batch GPU session count of 2 reached."
    sent, slept = run(tmp_path, Fake([{}]), replies=(full, "pushed"))
    assert len(sent) == 2 and len(slept) == 1


def test_other_push_errors_exit(tmp_path):
    with pytest.raises(SystemExit, match="push failed"):
        run(tmp_path, Fake([{}]), replies=("Kernel push error: bad slug",))


def test_notebooks_compare_by_cell_source():
    local = {"cells": [{"cell_type": "code", "source": ["a\n", "b"], "outputs": [1]}]}
    served = {"cells": [{"cell_type": "code", "source": "a\nb", "outputs": []}], "metadata": {}}
    assert ks.code_of(json.dumps(local)) == ks.code_of(json.dumps(served))


def test_report_lists_active_versions_and_unnamed_rows():
    lines = ks.report(Fake([{2: "RUNNING", 3: "QUEUED"}]))
    assert lines[:2] == ["RUNNING  me/a version 2", "QUEUED   me/a version 3"]
    assert lines[2].startswith("2 active") and "no name" in lines[3]


def test_patient_retries_only_rate_limits():
    class Limited(Exception):
        response = type("R", (), {"status_code": 429})()

    answers, slept = [Limited(), "ok"], []

    def call():
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    assert ks.patient(call, sleep=slept.append) == "ok" and slept == [5]
    with pytest.raises(OSError):
        ks.patient(lambda: (_ for _ in ()).throw(OSError("down")), sleep=slept.append)
