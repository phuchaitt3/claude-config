"""Push Kaggle kernels without leaving a queued run that holds a GPU session.

The account's 2 GPU sessions are shared by every project and machine. Pushing a kernel that already
has a queued or running version does not stop that version: the new one can sit QUEUED and still
count against the limit, and `kaggle kernels status <owner>/<kernel>` shows only the newest version
(standard: findings/kaggle-gpu-sessions, checked 2026-11-28).

    python ~/claude-config/scripts/kaggle_slots.py status
    python ~/claude-config/scripts/kaggle_slots.py push -p <folder> [--accelerator X] [--run-timeout S]

`push` waits on this machine, sending nothing, while the kernel has an active version or both
sessions are taken; run it in the background. It refuses code identical to an active version.
`--allow-active` skips both checks. If Kaggle cannot be read, nothing is pushed.

Pushes through this tool on one machine take turns: a local file lock (in gpu_run's lock folder) is
held around check-and-push only, never while waiting. Across machines (laptop and PC) the gap stays
open: Kaggle offers no lock, so two pushes within the same few seconds can both get through.

There is no way to cancel a version from here: use "View Active Events" on the Kaggle site.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gpu_run  # noqa: E402  (its file lock; standard library only)

DONE = {"COMPLETE", "ERROR", "CANCEL_ACKNOWLEDGED", "NEW_SCRIPT"}
LOOKBACK = 5  # newest versions of a kernel to check; the account runs 2 at once
RECENT = 20  # most recently run kernels `status` lists
RECENT_DAYS = 3  # older runs are not checked: a session ends within hours, and each check costs calls
LOCK_POLL = 2  # seconds between tries for the local push lock
BACKOFF = (5, 15, 30)  # seconds, after "429 Too Many Requests"
MAX_FAILURES = 5  # failed checks in a row, while waiting, before giving up
# The CLI prints a refused push as "Kernel push error: ..." and still exits 0.
SESSION_LIMIT = "Maximum batch GPU session count"
PUSH_ERROR = "Kernel push error"


def patient(call, sleep=time.sleep):
    """Run `call`, waiting and retrying while Kaggle answers 429."""
    for delay in (*BACKOFF, None):
        try:
            return call()
        except Exception as error:
            code = getattr(getattr(error, "response", None), "status_code", None)
            if code != 429 or delay is None:
                raise
            sleep(delay)


class Kaggle:
    """The few read calls needed, through `kagglesdk` (the CLI shows no version number)."""

    def __init__(self) -> None:
        from kaggle.api.kaggle_api_extended import KaggleApi

        self.api = KaggleApi()
        self.api.authenticate()
        self.owner = self.api.get_config_value("username")
        self._local = threading.local()

    def _kernels(self):
        if not hasattr(self._local, "client"):  # one client per thread
            self._local.client = self.api.build_kaggle_client().__enter__()
        return self._local.client.kernels.kernels_api_client

    def _get(self, ref: str, version: int | None = None):
        from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest

        request = ApiGetKernelRequest()
        request.user_name, request.kernel_slug = ref.split("/", 1)
        if version:
            request.version_label = f"v{version}"
        return self._kernels().get_kernel(request)

    def latest_version(self, ref: str) -> int:
        """0 for a kernel never pushed: Kaggle answers 403 or 404 for one that does not exist."""
        try:
            return patient(lambda: self._get(ref)).metadata.current_version_number
        except Exception as error:
            if getattr(getattr(error, "response", None), "status_code", None) in (403, 404):
                return 0
            raise

    def state(self, ref: str, version: int) -> str:
        from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelSessionStatusRequest

        request = ApiGetKernelSessionStatusRequest()
        request.user_name, request.kernel_slug = ref.split("/", 1)
        request.version_label = f"v{version}"
        return patient(lambda: self._kernels().get_kernel_session_status(request)).status.name

    def source(self, ref: str, version: int) -> str:
        return patient(lambda: self._get(ref, version)).blob.source

    def recent(self) -> tuple[list[str], int]:
        """Recently run kernels as `owner/slug`, and how many rows came without a name."""
        from kagglesdk.kernels.types.kernels_api_service import ApiListKernelsRequest
        from kagglesdk.kernels.types.kernels_enums import KernelsListSortType

        request = ApiListKernelsRequest()
        request.user = self.owner
        request.sort_by = KernelsListSortType.DATE_RUN
        request.page, request.page_size = 1, RECENT
        refs, unnamed = [], 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=RECENT_DAYS)
        for row in patient(lambda: self._kernels().list_kernels(request)).kernels or []:
            if row is None or not row.ref:
                unnamed += 1
                continue
            ran = row.last_run_time
            if ran and ran.replace(tzinfo=ran.tzinfo or timezone.utc) < cutoff:
                continue
            refs.append("/".join(row.ref.strip("/").split("/")[-2:]))
        return refs, unnamed


def active_versions(kaggle, ref: str) -> dict[int, str]:
    """{version: state} for the queued or running versions among the newest few."""
    latest = kaggle.latest_version(ref)
    found = {}
    for version in range(latest, max(latest - LOOKBACK, 0), -1):
        state = kaggle.state(ref, version)
        if state not in DONE:
            found[version] = state
    return found


def code_of(text: str) -> str:
    """Comparable code: a notebook by its cell sources (Kaggle rewrites outputs and metadata)."""
    try:
        cells = json.loads(text)["cells"]
        return json.dumps(
            [[c.get("cell_type"), "".join(c.get("source", ""))] for c in cells], ensure_ascii=False
        )
    except (ValueError, KeyError, TypeError, AttributeError):
        return text.replace("\r\n", "\n").rstrip("\n")


def read_kernel(folder: Path) -> tuple[str, str]:
    """(`owner/slug`, code) from the folder's `kernel-metadata.json`."""
    meta = json.loads((folder / "kernel-metadata.json").read_text(encoding="utf-8"))
    ref = str(meta.get("id", ""))
    if ref.count("/") != 1:
        sys.exit("kernel-metadata.json needs an `id` of the form owner/slug; nothing was pushed")
    return ref, (folder / meta["code_file"]).read_text(encoding="utf-8")


def send(command: list[str]) -> tuple[int, str]:
    out = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )  # fmt: skip
    return out.returncode, (out.stdout + out.stderr).strip()


def say(text: str) -> None:
    print(time.strftime("%H:%M:%S"), text, flush=True)


@contextlib.contextmanager
def push_lock(deadline: float, sleep, clock):
    """One check-and-push at a time on this machine. The OS frees the lock if its holder dies."""
    lock = gpu_run.Lock("kaggle-push")
    told = False
    while not lock.try_acquire({"pid": os.getpid()}):
        if clock() + LOCK_POLL >= deadline:
            sys.exit("gave up waiting (another push on this machine); nothing was pushed")
        if not told:
            say("waiting: another push on this machine is checking or sending")
            told = True
        sleep(LOCK_POLL)
    try:
        yield
    finally:
        lock.release()


def push(kaggle, args, send=send, sleep=time.sleep, clock=time.monotonic) -> None:
    folder = Path(args.path)
    ref, code = read_kernel(folder)
    command = ["kaggle", "kernels", "push", "-p", str(folder)]
    if args.accelerator:
        command += ["--accelerator", args.accelerator]
    if args.run_timeout:
        command += ["-t", str(args.run_timeout)]

    deadline = clock() + args.wait_timeout
    failures = 0

    def wait(why: str) -> None:
        if args.no_wait:
            sys.exit(f"{why}; nothing was pushed")
        if clock() + args.every >= deadline:
            sys.exit(f"gave up waiting ({why}); nothing was pushed")
        say(f"waiting: {why}")
        sleep(args.every)

    waited = False

    def attempt() -> str | None:
        """Check, then push. Returns why to wait, or None once the push is accepted."""
        nonlocal failures, waited
        if not args.allow_active:
            try:
                active = active_versions(kaggle, ref)
                same = [v for v in active if code_of(kaggle.source(ref, v)) == code_of(code)]
            except Exception as error:  # noqa: BLE001 (any unread state means: do not push)
                failures += 1
                if not waited or failures >= MAX_FAILURES:
                    sys.exit(f"could not check {ref} ({error}); nothing was pushed")
                return f"the check failed: {error}"
            failures = 0
            if same:
                sys.exit(
                    f"{ref} version {same[0]} is {active[same[0]]} with identical code; nothing "
                    "was pushed. Wait for it and read its output (--allow-active pushes anyway)."
                )
            if active:
                waited = True
                shown = ", ".join(f"version {v} {s}" for v, s in sorted(active.items()))
                return f"{ref} has {shown}"
        status, text = send(command)
        say(text)
        if SESSION_LIMIT in text:
            waited = True
            return "both GPU sessions are taken"
        if status != 0 or PUSH_ERROR in text:
            sys.exit("push failed; nothing was started")
        return None

    while True:
        with push_lock(deadline, sleep, clock):
            why = attempt()
        if why is None:
            return
        wait(why)  # outside the lock: other kernels' pushes go ahead meanwhile


def report(kaggle) -> list[str]:
    refs, unnamed = kaggle.recent()

    def read(ref: str):
        try:
            return ref, active_versions(kaggle, ref)
        except Exception as error:  # noqa: BLE001
            return ref, str(error)

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(read, refs))
    lines, count, unknown = [], 0, []
    for ref, found in results:
        if isinstance(found, str):
            unknown.append(f"UNKNOWN  {ref}: {found[:120]}")
            continue
        for version, state in sorted(found.items()):
            lines.append(f"{state:8} {ref} version {version}")
            count += 1
    lines += unknown
    lines.append(f"{count} active version(s) in {len(refs)} kernel(s) run in the last {RECENT_DAYS} days; "
                 "the account allows 2 GPU sessions (this count includes any CPU runs)")  # fmt: skip
    if unnamed:
        lines.append(f"{unnamed} listed kernel(s) have no name and were not checked")
    return lines


def tool_python() -> Path | None:
    """The interpreter of the `uv tool install kaggle` environment, which has `kagglesdk`."""
    uv = shutil.which("uv")
    if not uv:
        return None
    root = subprocess.run([uv, "tool", "dir"], capture_output=True, text=True).stdout.strip()
    if not root:
        return None
    for part in ("Scripts/python.exe", "bin/python"):
        path = Path(root) / "kaggle" / part
        if path.is_file():
            return path
    return None


def ensure_sdk() -> None:
    try:
        import kagglesdk  # noqa: F401
    except ImportError:
        python = tool_python()
        if not python or os.environ.get("KAGGLE_SLOTS_REEXEC"):
            sys.exit("no `kagglesdk` here; install the CLI with `uv tool install kaggle`")
        env = {**os.environ, "KAGGLE_SLOTS_REEXEC": "1"}
        sys.exit(subprocess.run([str(python), __file__, *sys.argv[1:]], env=env).returncode)


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    commands = top.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="every queued or running version on the account")
    p = commands.add_parser("push", help="push a kernel once it has no active version")
    p.add_argument("-p", "--path", required=True, help="folder with kernel-metadata.json")
    p.add_argument("--accelerator")
    p.add_argument("--run-timeout", type=int, help="kernel run limit, seconds")
    p.add_argument("--every", type=int, default=60, help="seconds between checks")
    p.add_argument("--wait-timeout", type=int, default=12 * 3600, help="seconds to wait in all")
    p.add_argument("--no-wait", action="store_true", help="exit instead of waiting")
    p.add_argument("--allow-active", action="store_true", help="push without checking")
    return top


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    ensure_sdk()
    kaggle = Kaggle()
    if args.command == "status":
        print("\n".join(report(kaggle)))
    else:
        push(kaggle, args)


if __name__ == "__main__":
    main()
