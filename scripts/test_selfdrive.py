"""Tests for scripts/selfdrive.ps1: the prompt built with and without each option, and the
low-disk refusal (uses -DryRun)."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("selfdrive.ps1")
PWSH = shutil.which("pwsh") or shutil.which("powershell")
pytestmark = pytest.mark.skipif(PWSH is None, reason="PowerShell not available")


@pytest.fixture()
def repo(tmp_path):
    d = tmp_path / "demo" / "main"
    (d / ".git").mkdir(parents=True)
    return d


def invoke(repo, *args, free_gb=100):
    return subprocess.run(
        [PWSH, "-NoProfile", "-File", str(SCRIPT), str(repo), "-DryRun", *args],
        capture_output=True, text=True, timeout=60,
        env={**os.environ, "SELFDRIVE_TEST_FREE_GB": str(free_gb)})


def run(repo, *args, **kwargs):
    out = invoke(repo, *args, **kwargs)
    assert out.returncode == 0, out.stderr
    return dict(line.split("=", 1) for line in out.stdout.splitlines() if "=" in line)


def test_plain_prompt(repo):
    p = run(repo)["PROMPT"]
    assert "Load workflow:self-drive and follow Overnight mode." in p
    assert "Work only these issues" not in p and "Brief for tonight" not in p


def test_issues_listed_in_order(repo):
    p = run(repo, "-Issues", "285,245")["PROMPT"]
    assert "Work only these issues, in this order: #285, #245." in p


def test_brief_file_appended(repo, tmp_path):
    f = tmp_path / "tonight.md"
    f.write_text("Skip the docs.", encoding="utf-8")
    p = run(repo, "-Brief", str(f))["PROMPT"]
    assert p.endswith("Brief for tonight (from tonight.md): Skip the docs.")
    assert "Work only these issues" not in p


def test_issues_and_brief_together(repo, tmp_path):
    f = tmp_path / "b.md"
    f.write_text("Be careful.", encoding="utf-8")
    p = run(repo, "-Issues", "7", "-Brief", str(f))["PROMPT"]
    assert "#7." in p and p.endswith("Be careful.")


def test_missing_brief_fails(repo):
    out = invoke(repo, "-Brief", "nope.md")
    assert out.returncode != 0


def test_low_disk_refused(repo):
    out = invoke(repo, free_gb=29)
    assert out.returncode != 0
    assert "-LowDiskOk" in out.stderr


@pytest.mark.parametrize("args, free_gb", [((), 30), (("-LowDiskOk",), 5), (("-ReadyOnly",), 5)])
def test_low_disk_allowed(repo, args, free_gb):
    assert run(repo, *args, free_gb=free_gb)["PROMPT"]
