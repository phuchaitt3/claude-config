"""Monthly rotation and reading of the ~/.gpu-guard logs (claude-config issue #17). Stdlib only.

``thermal.jsonl`` stays the current file, so everything that tails it keeps working. The thermal
logger, its only writer, calls ``rotate_months`` at start and when the month changes: lines from
earlier months move to ``thermal-YYYY-MM.jsonl``. Readers call ``read_rows`` and get the archives
that cover the window plus the current file. Archives are kept (the cooling comparison in
findings/laptop-cooling-baseline needs months of history).
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

WARN_BYTES = 50 * 1024 * 1024  # the issue's trigger: thermal.jsonl over 50 MB


def _month(ts: str) -> str | None:
    m = re.match(r"(\d{4}-\d{2})-\d{2}T", ts or "")
    return m.group(1) if m else None


def rotate_months(d: Path, name: str = "thermal.jsonl") -> int:
    """Move lines of months before the current one out of ``name`` into ``<stem>-YYYY-MM<suffix>``.
    Returns the number of lines moved. Never raises; the caller must be the file's only writer."""
    path = d / name
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        current = datetime.now().astimezone().strftime("%Y-%m")
        keep, old = [], {}
        for line in lines:
            try:
                month = _month(json.loads(line).get("ts", ""))
            except (ValueError, AttributeError):
                month = None
            if month and month < current:
                old.setdefault(month, []).append(line)
            else:  # current month, or a line with no readable month: stays
                keep.append(line)
        if not old:
            return 0
        stem, suffix = Path(name).stem, Path(name).suffix
        for month, rows in old.items():
            with open(d / f"{stem}-{month}{suffix}", "a", encoding="utf-8") as f:
                f.write("\n".join(rows) + "\n")
        tmp = d / (name + ".tmp")
        tmp.write_text("".join(x + "\n" for x in keep), encoding="utf-8")
        os.replace(tmp, path)
        return sum(len(r) for r in old.values())
    except OSError:
        return 0


def log_files(d: Path, name: str, since: datetime) -> list[Path]:
    """Archives whose month is not before ``since``'s month, oldest first, then the current file."""
    stem, suffix = Path(name).stem, Path(name).suffix
    first = since.strftime("%Y-%m")
    out = []
    for p in sorted(d.glob(f"{stem}-????-??{suffix}")):
        if p.name[len(stem) + 1:len(stem) + 8] >= first:
            out.append(p)
    return out + [d / name]


def read_rows(d: Path, name: str, since: datetime) -> list[dict]:
    """JSON rows with ``ts`` >= since, from the archives covering the window and the current file."""
    rows: list[dict] = []
    for p in log_files(d, name, since):
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                row = json.loads(line)
                if datetime.fromisoformat(row["ts"]) >= since:
                    rows.append(row)
            except (ValueError, KeyError):
                continue
    return rows


def size_report(d: Path) -> list[str]:
    """One line per log file (current and archives) with its size; a warning when one is over WARN_BYTES."""
    out = []
    for p in sorted(d.glob("*.jsonl")):
        size = p.stat().st_size
        warn = f"  WARNING: over {WARN_BYTES // 2**20} MB, see claude-config issue #17" if size > WARN_BYTES else ""
        out.append(f"  {p.name}: {size / 2**20:.2f} MB{warn}")
    return out
