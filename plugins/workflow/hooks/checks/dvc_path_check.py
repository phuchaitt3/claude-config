"""Check: warn when a repository's DVC remote path will break or silently not sync.

User's yes, 2026-11-28, after a OneDrive folder moved and a remote under the old folder kept
reporting "in sync" while nothing was uploaded. Once a day per repository it warns when:
- the tracked `.dvc/config` holds an absolute local path (the path belongs in the global DVC
  config of each machine; `workflow:new-project`, "Folder layout"), or
- the remote in effect is inside a folder named OneDrive that is not a folder OneDrive syncs.

Reminder only: it never blocks. Only local paths are ever printed, never other remote URLs.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path, PureWindowsPath

EVENTS = {"UserPromptSubmit"}
CACHE = Path.home() / ".claude" / "hook-cache" / "dvc-path.json"

_SECTION = re.compile(r"""^\[\s*'?\s*(core|remote\s+"([^"]+)")\s*'?\s*\]$""")
_ABSOLUTE = re.compile(r"^(?:[A-Za-z]:[\\/]|/|\\\\|~)")


def global_config() -> Path | None:
    base = os.environ.get("DVC_GLOBAL_CONFIG_DIR")
    if base:
        return Path(base) / "config"
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "iterative" / "dvc" / "config"
    return Path.home() / ".config" / "dvc" / "config"


def parse(path: Path | None) -> tuple[str | None, dict[str, str]]:
    """(default remote name, {remote name: url}) of one DVC config file."""
    default, urls, section = None, {}, None
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace") if path else ""
    except OSError:
        text = ""
    for line in (l.strip() for l in text.splitlines()):
        m = _SECTION.match(line)
        if line.startswith("["):
            section = (m.group(2) or "core") if m else None
            continue
        key, sep, value = (p.strip() for p in line.partition("="))
        if not sep or section is None:
            continue
        if section == "core" and key == "remote":
            default = value
        elif section != "core" and key == "url":
            urls[section] = value
    return default, urls


def onedrive_folders() -> list[str]:
    """The folders OneDrive syncs on this machine; empty when unknown."""
    try:
        import winreg
    except ImportError:
        return []
    found = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\OneDrive\Accounts") as root:
            for i in range(winreg.QueryInfoKey(root)[0]):
                try:
                    with winreg.OpenKey(root, winreg.EnumKey(root, i)) as account:
                        found.append(winreg.QueryValueEx(account, "UserFolder")[0])
                except OSError:
                    continue
    except OSError:
        pass
    return [f for f in found if f]


def outside_sync(url: str, synced: list[str]) -> bool:
    path = PureWindowsPath(url)  # case-insensitive, accepts both slashes
    if not synced or not any(p.lower().startswith("onedrive") for p in path.parts):
        return False
    return not any(path.is_relative_to(PureWindowsPath(s)) for s in synced)


def problems(repo: Path, global_path: Path | None, synced: list[str]) -> list[str]:
    tracked = repo / ".dvc" / "config"
    if not tracked.is_file():
        return []
    found = []
    t_default, t_urls = parse(tracked)
    for name, url in t_urls.items():
        if _ABSOLUTE.match(url):
            found.append(f".dvc/config commits the absolute path {url} for remote {name}; move it to "
                         f"`dvc remote add --global` and commit only the remote name")
    g_default, urls = parse(global_path)
    l_default, l_urls = parse(repo / ".dvc" / "config.local")
    urls.update(t_urls)
    urls.update(l_urls)
    name = l_default or t_default or g_default
    url = urls.get(name or "", "")
    if _ABSOLUTE.match(url) and outside_sync(url, synced):
        found.append(f"DVC remote {name} is {url}, outside the folder OneDrive syncs "
                     f"({', '.join(synced)}): nothing there is uploaded")
    return found


def repo_root(cwd: Path) -> Path | None:
    for folder in (cwd, *cwd.parents):
        if (folder / ".git").exists():
            return folder
    return None


def run(payload, today: date | None = None, cache: Path = CACHE, global_path: Path | None = None,
        synced: list[str] | None = None):
    repo = repo_root(Path(payload.get("cwd") or "."))
    if repo is None or not (repo / ".dvc" / "config").is_file():
        return None
    today = (today or date.today()).isoformat()
    try:
        seen = json.loads(cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        seen = {}
    if seen.get(str(repo)) == today:
        return None
    seen[str(repo)] = today
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(seen), encoding="utf-8")
    except OSError:
        pass
    found = problems(repo, global_path or global_config(),
                     onedrive_folders() if synced is None else synced)
    if not found:
        return None
    return ("dvc-path (daily): " + "; ".join(found) +
            ". Mention it once; do not interrupt the user's task for it.")
