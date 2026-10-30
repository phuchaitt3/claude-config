import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location("merge_settings", Path(__file__).with_name("merge_settings.py"))
assert _spec and _spec.loader
merge_settings = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(merge_settings)

REPO = "C:\\Users\\x\\claude-config"


def test_empty_settings_get_the_marketplace_autoupdate_and_plugin() -> None:
    settings: dict = {}
    changes = merge_settings.merge(settings, REPO)
    assert len(changes) == 3
    assert settings["extraKnownMarketplaces"]["personal-config"] == {
        "source": {"source": "directory", "path": REPO},
        "autoUpdate": True,
    }
    assert settings["enabledPlugins"]["workflow@personal-config"] is True


def test_merge_is_idempotent_and_keeps_other_settings() -> None:
    settings = {"model": "opus", "hooks": {"Stop": []}, "enabledPlugins": {"other@x": True}}
    merge_settings.merge(settings, REPO)
    assert merge_settings.merge(settings, REPO) == []
    assert settings["model"] == "opus" and settings["hooks"] == {"Stop": []}
    assert settings["enabledPlugins"]["other@x"] is True


def run(settings: Path) -> subprocess.CompletedProcess[str]:
    script = Path(merge_settings.__file__)
    return subprocess.run(
        [sys.executable, str(script), "--settings", str(settings), "--repo", REPO],
        capture_output=True, text=True, check=False,
    )


def test_cli_writes_a_backup_then_reports_no_change(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"model": "sonnet"}), encoding="utf-8")
    first = run(settings)
    assert first.returncode == 0 and "autoUpdate on" in first.stdout
    assert len(list(tmp_path.glob("settings.json.bak-*"))) == 1
    assert json.loads(settings.read_text(encoding="utf-8"))["model"] == "sonnet"
    assert "no change" in run(settings).stdout


def test_cli_refuses_to_touch_invalid_json(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text("{ not json", encoding="utf-8")
    result = run(settings)
    assert result.returncode == 1 and settings.read_text(encoding="utf-8") == "{ not json"
