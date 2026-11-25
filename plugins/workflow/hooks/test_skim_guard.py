import importlib.util
import io
import json
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("skim_guard", Path(__file__).with_name("skim_guard.py"))
assert _spec and _spec.loader
skim_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(skim_guard)

ROOT = "D:\\work\\notes\\main"
OTHER = "D:\\work\\tool\\main"


def call(tool, project=OTHER, cwd=OTHER, **args):
    return skim_guard.refusal({"tool_name": tool, "tool_input": args, "cwd": cwd}, project, [ROOT])


@pytest.mark.parametrize("path", [
    "D:\\work\\notes\\main\\topics\\a.md", "d:/work/notes/main/CLAUDE.md", "/d/work/notes/main/plan.md",
    "D:/work/tool/main/../../notes/main/a.md",
])
def test_refuses_edits_inside(path):
    assert call("Edit", file_path=path)
    assert call("Write", file_path=path)
    assert call("NotebookEdit", notebook_path=path)


def test_relative_edit_uses_cwd():
    assert call("Edit", cwd=ROOT, file_path="a.md")
    assert not call("Edit", file_path="a.md")


@pytest.mark.parametrize("path", ["D:\\work\\notes\\main2\\a.md", "D:\\work\\notes\\a.md", "D:\\work\\tool\\main\\a.md"])
def test_allows_edits_elsewhere(path):
    assert not call("Edit", file_path=path)


@pytest.mark.parametrize("command", [
    "cd /d/work/notes/main && git status", "sed -i s/a/b/ D:/work/notes/main/a.md", 'rm "D:\\work\\notes\\main\\a.md"',
    "cd /d/work; echo x > notes/main/a.md", "python -c \"open('D:\\\\work\\\\notes\\\\main\\\\a.md','w')\"",
    "git -C /D/Work/Notes/Main commit -m x", "cd D:/work/notes/main",
])
def test_refuses_shell_naming_the_folder(command):
    assert call("Bash", command=command)
    assert call("PowerShell", command=command)


def test_refuses_shell_inside_the_folder():
    assert call("Bash", cwd=ROOT + "\\topics", command="ls")


@pytest.mark.parametrize("command", [
    "ls", "git status", "cd /d/work/tool/main && ls", "cat D:/work/notes/main2/a.md", "gh issue list -R me/notes",
    "cat D:/work/my-notes/main/a.md", "ls D:/work/notes/other",
])
def test_allows_other_shell(command):
    assert not call("Bash", command=command)


def test_own_chats_are_left_to_the_project_hooks():
    assert not call("Edit", project="d:/work/notes/main", cwd=ROOT, file_path=ROOT + "\\a.md")
    assert not call("Bash", project=ROOT, cwd=ROOT, command="rm a.md")


def test_reading_is_allowed():
    assert not call("Read", file_path=ROOT + "\\a.md")


def run_main(monkeypatch, capsys, registry, payload):
    monkeypatch.setattr(skim_guard, "REGISTRY", registry)
    monkeypatch.setattr(skim_guard, "flagged_roots", lambda r=registry: _flagged(registry))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", OTHER)
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    assert skim_guard.main() == 0
    return capsys.readouterr().out


_flagged = skim_guard.flagged_roots


def test_main_follows_list_and_flag(monkeypatch, capsys, tmp_path):
    registry, repo = tmp_path / "roots.json", tmp_path / "notes" / "main"
    (repo / ".claude").mkdir(parents=True)
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": str(repo / "a.md")}, "cwd": OTHER})
    assert run_main(monkeypatch, capsys, registry, payload) == ""  # no list
    registry.write_text(json.dumps([str(repo)]))
    assert run_main(monkeypatch, capsys, registry, payload) == ""  # listed, flag gone
    (repo / ".claude" / "skim-mode").write_text("on")
    assert '"deny"' in run_main(monkeypatch, capsys, registry, payload)
    assert run_main(monkeypatch, capsys, registry, "not json") == ""
    registry.write_text("broken")
    assert run_main(monkeypatch, capsys, registry, payload) == ""
