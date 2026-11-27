"""Tests for scripts/selfdrive-queue.ps1 (the saved-run menu) and scripts/queue-shortcut.ps1.

gh is replaced by a JSON file (SELFDRIVE_TEST_ISSUES); runs are started with -DryRun only."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
PWSH = shutil.which("pwsh") or shutil.which("powershell")
pytestmark = pytest.mark.skipif(PWSH is None, reason="PowerShell not available")

BODY = "Issues: #273, #245\n\nFollow each open PR.\n\nSecond \"quoted\" paragraph."


def issue(number=12, body=BODY, repo="demo", association="COLLABORATOR", created="2026-11-20T05:00:00Z"):
    return {"repository": {"name": repo, "nameWithOwner": f"me/{repo}"}, "number": number,
            "title": f"Saved run {number}", "body": body, "createdAt": created,
            "authorAssociation": association}


@pytest.fixture()
def root(tmp_path):
    d = tmp_path / "root" / "demo" / "main"
    d.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    subprocess.run(["git", "-C", str(d), "remote", "add", "origin", "https://github.com/me/demo.git"],
                   check=True)
    return tmp_path / "root"


def invoke(root, issues, *args, free_gb=100, machine="laptop", stdin=None):
    data = root.parent / "issues.json"
    data.write_text(json.dumps(issues), encoding="utf-8")
    env = {**os.environ, "SELFDRIVE_ROOT": str(root), "SELFDRIVE_TEST_ISSUES": str(data),
           "SELFDRIVE_TEST_FREE_GB": str(free_gb), "SELFDRIVE_TEST_MACHINE": machine, "NO_COLOR": "1"}
    return subprocess.run(
        [PWSH, "-NoProfile", "-File", str(HERE / "selfdrive-queue.ps1"), "-DryRun", *args],
        capture_output=True, text=True, timeout=90, env=env, input=stdin)


def test_list_shows_runs_oldest_first_without_starting(root):
    out = invoke(root, [issue(30, created="2026-11-22T05:00:00Z"), issue(12)], "-List")
    assert out.returncode == 0, out.stdout + out.stderr
    assert "1) demo#12  saved 2026-11-20  issues: #273 #245" in out.stdout
    assert "2) demo#30" in out.stdout
    assert "CANNOT" not in out.stdout and "PROMPT=" not in out.stdout


@pytest.mark.parametrize("pick", ["1", "demo#12", "me/demo#12"])
def test_pick_passes_issues_and_brief_to_selfdrive(root, pick):
    out = invoke(root, [issue()], "-Pick", pick)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "Work only these issues, in this order: #273, #245." in out.stdout
    assert "This is saved run me/demo#12" in out.stdout
    assert 'Second "quoted" paragraph.' in out.stdout
    assert f"DIR={root / 'demo' / 'main'}" in out.stdout


def test_typed_number_starts_that_run(root):
    out = invoke(root, [issue()], stdin="1\n\n")
    assert "PROMPT=" in out.stdout, out.stdout + out.stderr


def test_enter_quits_without_starting(root):
    out = invoke(root, [issue()], stdin="\n\n")
    assert out.returncode == 0 and "PROMPT=" not in out.stdout


@pytest.mark.parametrize("kwargs, body, repo, reason", [
    ({"free_gb": 29}, BODY, "demo", "Only 29 GB free"),
    ({"machine": "desktop"}, "Issues: 1\nMachine: laptop\n\nx", "demo", "needs the laptop"),
    ({}, BODY, "other", "no checkout of me/other"),
    ({}, "Just do it.", "demo", "cannot read this header line"),
    ({}, "Machine: any\n\nx", "demo", "no 'Issues:"),
])
def test_run_this_machine_cannot_do_is_marked_and_refused(root, kwargs, body, repo, reason):
    runs = [issue(body=body, repo=repo)]
    listed = invoke(root, runs, "-List", **kwargs)
    assert "CANNOT RUN HERE" in listed.stdout and reason in listed.stdout, listed.stdout
    picked = invoke(root, runs, "-Pick", "1", **kwargs)
    assert picked.returncode == 1 and "PROMPT=" not in picked.stdout


def test_machine_line_matching_this_machine_runs(root):
    out = invoke(root, [issue(body="Issues: 7\r\nMachine: laptop\r\n\r\nBrief.")], "-Pick", "1")
    assert "#7." in out.stdout and out.returncode == 0, out.stdout


def test_author_without_write_access_is_not_listed(root):
    out = invoke(root, [issue(association="NONE")], "-List")
    assert "Ignored 1 issue(s)" in out.stdout and "demo#12" not in out.stdout


def test_empty_queue(root):
    out = invoke(root, [], "-List")
    assert out.returncode == 0 and "queue is empty" in out.stdout


def test_unknown_pick_fails(root):
    out = invoke(root, [issue()], "-Pick", "5")
    assert out.returncode == 1 and "No single saved run" in out.stdout


@pytest.mark.skipif(sys.platform != "win32", reason="Windows shortcut")
def test_shortcut_created_in_the_given_folder(tmp_path):
    for _ in range(2):
        out = subprocess.run(
            [PWSH, "-NoProfile", "-File", str(HERE / "queue-shortcut.ps1"), "-Desktop", str(tmp_path)],
            capture_output=True, text=True, timeout=60)
        assert out.returncode == 0, out.stderr
    assert (tmp_path / "Self-drive queue.lnk").is_file()
