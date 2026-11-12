import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("search_guard", Path(__file__).with_name("search_guard.py"))
assert _spec and _spec.loader
search_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(search_guard)


@pytest.mark.parametrize(
    "command",
    [
        "find / -maxdepth 6 -name 'laptop_base*' -mmin -15",
        "find / -ipath '*site-packages/transformers/masking_utils.py'",
        "find /c -name foo",
        "find /d/ -type f",
        "find C:\\ -name foo",
        "find ~ -name foo",
        "find / -name a 2>/dev/null | head",
        "cd x && find / -name a",
        "timeout 60 find / -name a",
        "/usr/bin/find / -name a",
        "grep -r pattern /",
        "grep -rn pattern /d",
        "rg pattern C:\\",
        "Get-ChildItem C:\\ -Recurse -Filter *.py",
        "gci -Recurse C:/",
    ],
)
def test_whole_drive_search_is_refused(command: str) -> None:
    assert "Refused" in search_guard.refusal(command)


@pytest.mark.parametrize(
    "command",
    [
        "find . -name '*.py'",
        "find ./src -name x",
        "find /d/1.git_projs/thesis/main -name x",
        "find packages -maxdepth 2",
        "find -name x",
        "grep -rn pattern src",
        "grep pattern /etc/hosts",
        "rg pattern",
        "git log --oneline",
        "ls /",
        "Get-ChildItem . -Recurse",
        "Get-ChildItem C:\\Users\\x\\proj -Recurse",
        "python -c \"print('find / -name x')\"",
        "echo find / done",
    ],
)
def test_scoped_search_is_allowed(command: str) -> None:
    assert search_guard.refusal(command) == ""
