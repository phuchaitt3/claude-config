import importlib.util
from datetime import date
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "dvc_path_check", Path(__file__).with_name("dvc_path_check.py"))
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

SYNCED = [r"D:\OneDrive"]
DAY = date(2026, 11, 28)


def repo(tmp_path, tracked, local=None, global_=None):
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    (root / ".dvc").mkdir()
    (root / ".dvc" / "config").write_text(tracked, encoding="utf-8")
    if local:
        (root / ".dvc" / "config.local").write_text(local, encoding="utf-8")
    g = tmp_path / "global"
    g.write_text(global_ or "", encoding="utf-8")
    return root, g


def remote(url, name="r", default=True):
    core = f"[core]\n    remote = {name}\n" if default else ""
    return f"{core}['remote \"{name}\"']\n    url = {url}\n"


def run(tmp_path, root, g, synced=SYNCED, day=DAY):
    return m.run({"cwd": str(root)}, day, tmp_path / "cache.json", g, synced)


def test_silent_when_only_the_name_is_committed_and_path_is_synced(tmp_path):
    root, g = repo(tmp_path, "[core]\n    remote = r\n",
                   global_=remote("D:/onedrive/dvc/x", default=False))
    assert run(tmp_path, root, g) is None


def test_warns_on_committed_absolute_path(tmp_path):
    root, g = repo(tmp_path, remote("D:/OneDrive/dvc/x"))
    out = run(tmp_path, root, g)
    assert "commits the absolute path D:/OneDrive/dvc/x" in out and "outside" not in out


def test_warns_when_global_path_is_outside_the_synced_folder(tmp_path):
    root, g = repo(tmp_path, "[core]\n    remote = r\n",
                   global_=remote("C:/Users/u/OneDrive/dvc/x", default=False))
    out = run(tmp_path, root, g)
    assert "outside the folder OneDrive syncs" in out and "commits" not in out


def test_config_local_overrides_the_committed_path(tmp_path):
    root, g = repo(tmp_path, remote("C:/Users/u/OneDrive/dvc/x"),
                   local=remote("D:/OneDrive/dvc/x", default=False))
    assert "outside the folder" not in run(tmp_path, root, g)


def test_non_local_and_relative_urls_are_not_flagged_or_printed(tmp_path):
    root, g = repo(tmp_path, remote("s3://bucket/OneDrive"))
    assert run(tmp_path, root, g) is None
    root, g = repo(tmp_path / "b", remote("../store"))
    assert run(tmp_path / "b", root, g) is None


def test_unknown_sync_folder_skips_the_onedrive_warning(tmp_path):
    root, g = repo(tmp_path, "[core]\n    remote = r\n",
                   global_=remote("C:/Users/u/OneDrive/dvc/x", default=False))
    assert run(tmp_path, root, g, synced=[]) is None


def test_once_a_day_and_quiet_without_dvc(tmp_path):
    root, g = repo(tmp_path, remote("D:/OneDrive/dvc/x"))
    assert run(tmp_path, root, g)
    assert run(tmp_path, root, g) is None
    assert run(tmp_path, root, g, day=date(2026, 11, 29))
    (root / ".dvc" / "config").unlink()
    assert run(tmp_path, root, g, day=date(2026, 11, 30)) is None
