"""Print one merged timeline for a night: what the daemon, the GPU/RAM lock, the thermal logger,
the harness and each background session recorded, in local time.

Run it as the first step of the morning review of an overnight run:

    python ~/claude-config/scripts/night_timeline.py              # last evening 18:00 to now
    python ~/claude-config/scripts/night_timeline.py --since 2026-11-18T18:00 --until 2026-11-19T10:00

Sources (all read-only, none is changed):
- ~/.claude/daemon.log: spawn, retire (with its reason, e.g. `[low memory]`), settled, supervisor
  shutdown (times are UTC);
- ~/.gpu-guard/events.jsonl: lock start/end, refusals, unguarded use (`clock_cap_left_on` is noise
  and is left out);
- ~/.gpu-guard/thermal*.jsonl: `low_memory` rows, plus one summary line for the lowest
  `mem_phys_free_gb` in the window with the biggest memory users at that moment;
- session transcripts under ~/.claude/projects: the harness notice "was stopped because the system
  is running low on memory";
- ~/.claude/jobs/*/state.json: each session's name, state and last update.

Found 2026-11-19: the daemon itself retires idle workers under low memory and exits when no
workers remain, so a later `claude stop` fails with "service may be restarting".
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

KILL_TEXT = "was stopped because the system is running low on memory"
NOISE_EVENTS = {"clock_cap_left_on"}
_DAEMON = re.compile(r"^\[(\d{4}-\d\d-\d\dT[\d:.]+Z)\]\s*(.*)$")
_DAEMON_KEEP = re.compile(r"spawned|retire|settled|shutting down|daemon start|exiting|killed")


def parse_ts(value: str) -> datetime | None:
    """An ISO timestamp (Z or offset) as an aware datetime; naive values count as local time."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    return dt.astimezone() if dt.tzinfo is None else dt


def _jsonl(path: Path):
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict):
                    yield row
    except OSError:
        return


def daemon_rows(claude: Path, lo: datetime, hi: datetime) -> list[tuple[datetime, str, str]]:
    out = []
    try:
        lines = (claude / "daemon.log").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    for line in lines:
        m = _DAEMON.match(line)
        if not m or not _DAEMON_KEEP.search(m.group(2)):
            continue
        ts = parse_ts(m.group(1))
        if ts and lo <= ts <= hi:
            out.append((ts, "daemon", re.sub(r"^\[(bg|supervisor)\]\s*", "", m.group(2))))
    return out


def lock_rows(gpu: Path, lo: datetime, hi: datetime) -> list[tuple[datetime, str, str]]:
    out = []
    for row in _jsonl(gpu / "events.jsonl"):
        ts = parse_ts(str(row.get("ts", "")))
        event = str(row.get("event", ""))
        if not ts or not lo <= ts <= hi or event in NOISE_EVENTS:
            continue
        bits = [event]
        for key in ("resource", "purpose", "pid", "reason", "exit", "waited_s", "source"):
            if key in row:
                bits.append(f"{key}={row[key]}")
        out.append((ts, "lock", " ".join(bits)))
    return out


def thermal_rows(gpu: Path, lo: datetime, hi: datetime) -> list[tuple[datetime, str, str]]:
    out = []
    lowest: tuple[float, datetime, dict] | None = None
    for path in sorted(gpu.glob("thermal*.jsonl")):
        for row in _jsonl(path):
            ts = parse_ts(str(row.get("ts", "")))
            if not ts or not lo <= ts <= hi:
                continue
            if row.get("event") == "low_memory":
                out.append((ts, "thermal", f"low_memory phys_free={row.get('mem_phys_free_gb')} GB "
                                           f"top={row.get('top_mem_mb')}"))
            free = row.get("mem_phys_free_gb")
            if isinstance(free, (int, float)) and (lowest is None or free < lowest[0]):
                lowest = (float(free), ts, row)
    if lowest:
        free, ts, row = lowest
        out.append((ts, "thermal", f"lowest mem_phys_free_gb in window = {free} "
                                   f"(commit free {row.get('mem_free_gb')}) top={row.get('top_mem_mb')}"))
    return out


def transcript_rows(claude: Path, lo: datetime, hi: datetime) -> list[tuple[datetime, str, str]]:
    out = []
    since = lo.timestamp() - 3600
    for path in (claude / "projects").glob("*/*.jsonl"):
        try:
            if path.stat().st_mtime < since:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if KILL_TEXT not in text:
            continue
        for line in text.splitlines():
            if KILL_TEXT not in line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            ts = parse_ts(str(row.get("timestamp", ""))) if isinstance(row, dict) else None
            if ts and lo <= ts <= hi:
                out.append((ts, "harness", f"{KILL_TEXT} (session {path.parent.name[-30:]}/{path.stem[:8]})"))
    return out


def state_rows(claude: Path, lo: datetime, hi: datetime) -> list[tuple[datetime, str, str]]:
    out = []
    for path in (claude / "jobs").glob("*/state.json"):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        ts = parse_ts(str(d.get("updatedAt", "")))
        if ts and lo <= ts <= hi:
            out.append((ts, "session", f"{d.get('name')} [{path.parent.name}] state={d.get('state')} "
                                       f"detail={str(d.get('detail'))[:100]}"))
    return out


def collect(claude: Path, gpu: Path, lo: datetime, hi: datetime) -> list[tuple[datetime, str, str]]:
    rows = (daemon_rows(claude, lo, hi) + lock_rows(gpu, lo, hi) + thermal_rows(gpu, lo, hi)
            + transcript_rows(claude, lo, hi) + state_rows(claude, lo, hi))
    return sorted(set(rows), key=lambda r: r[0])


def default_window(now: datetime) -> tuple[datetime, datetime]:
    start = now.replace(hour=18, minute=0, second=0, microsecond=0)
    if start > now:
        start -= timedelta(days=1)
    return start, now


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--since", help="local ISO time (default: 18:00 of the last evening)")
    ap.add_argument("--until", help="local ISO time (default: now)")
    ap.add_argument("--claude-dir", default=str(Path.home() / ".claude"))
    ap.add_argument("--gpu-dir", default=str(Path.home() / ".gpu-guard"))
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    now = datetime.now(timezone.utc).astimezone()
    lo, hi = default_window(now)
    if args.since:
        lo = parse_ts(args.since) or lo
    if args.until:
        hi = parse_ts(args.until) or hi
    rows = collect(Path(args.claude_dir), Path(args.gpu_dir), lo, hi)
    print(f"Timeline {lo:%Y-%m-%d %H:%M} to {hi:%Y-%m-%d %H:%M} local, {len(rows)} entries")
    for ts, source, text in rows:
        print(f"{ts.astimezone():%m-%d %H:%M:%S}  {source:<8} {text[:240]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
