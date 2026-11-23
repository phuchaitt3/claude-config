---
topic: uv-cache-management
area: Software process
question: Is clearing the uv package cache on a schedule good practice, or how else is its size managed?
checked: 2026-11-23
review_months: 12
status: current
---
# Managing the uv package cache

- **Question:** The uv cache keeps filling a small system drive. Is clearing it on a schedule good practice, or is there a better way to manage it?
- **Finding:**
  - **uv's own docs do not tell users to clear the cache on a schedule.** `uv cache prune` removes only unused entries and "is safe to run periodically"; `uv cache clean` removes everything. The docs give no size figure and no cleaning schedule. The one routine they recommend is for CI: run `uv cache prune --ci` at the end of a job (drops pre-built wheels, keeps wheels built from source), because re-downloading wheels is often faster than caching them.
  - **The cache is what makes installs fast, so emptying it on a timer only moves the cost** (a re-download and re-unpack on the next sync) and it refills. Growth is a normal result of using many projects and package versions (large wheels such as ML libraries dominate). *Checker's inference:* prune when space is needed, not on a clock.
  - **Place the cache on the same filesystem as the environments.** The docs say that otherwise uv "cannot link files from the cache into the environment and must fall back to slower copy operations". A community report (a pull request in another project) adds that forcing `UV_LINK_MODE=hardlink` across drives does not help, because uv silently falls back to copy. *Checker's inference:* a cache on one drive and virtual environments on another means every environment holds a full copy and the cache is a second copy, so moving the cache to the environments' drive (`UV_CACHE_DIR`) saves more space than pruning. With the default link modes, pruning does not break existing environments.
  - **Moving it:** set `UV_CACHE_DIR` (or `--cache-dir`, or `tool.uv.cache-dir`). Changing it does not move or delete the old cache: run `uv cache clean --cache-dir <old path>` once the new location works. Never delete files inside the cache by hand.
  - **Practical routine:** leave the cache alone; run `uv cache prune` when a drive is short of space; put the cache beside the environments; use `uv cache clean <package>` to drop one heavy package.
  - **What a cold cache costs (added 2026-11-23):** `pip cache purge` empties both pip's wheel and HTTP caches (pip docs). Installed environments keep working; the cost is one re-download (and re-build of any source-built wheel) per package on its next install, not a permanent slowdown. Single-machine tests found a cold install about 1.9x a warm one for pip (about 10.9 s against 4.1 s) and far more for uv (about 5.7 s against 0.05 s, because uv's warm path is nearly free); the authors say download time and network speed dominate the cold figure. `uv cache prune` removes only unreachable entries (what the current environments use stays), so it costs less than `uv cache clean`; `--ci` drops downloaded wheels and keeps source-built ones. *Checker's inference:* a purge when space is short costs one slow install; purging on a short timer repeats that cost each time and hurts most for multi-GB wheels (torch), so a free-space threshold (clean only when a drive is nearly full) is not a schedule, but a calendar-based purge would be.
- **Evidence strength:** *official standard* (uv docs) for the commands, `--ci` advice and same-filesystem point; *anecdotal* for the cross-drive fallback report and the cold-cache timings (single runs by individual authors, one behind a paywall, read through search summaries); the space and "do not clean on a schedule" conclusions are the checker's own inference.
- **Sources:**
  - [uv docs, caching](https://docs.astral.sh/uv/concepts/cache/) (official docs)
  - [pydevtools handbook, how to manage uv's cache size](https://pydevtools.com/handbook/how-to/how-to-manage-uv-cache-size/) (community guide; moving the cache, venvs survive pruning; seen through search summary only)
  - [pip docs, caching](https://pip.pypa.io/en/stable/topics/caching/) (official docs; what `pip cache purge` clears)
  - [pythonspeed, making pip installs a little less slow](https://pythonspeed.com/articles/faster-pip-installs) (blog; cold against warm pip timings)
  - [Plain English, uv against pip with a cleared cache](https://python.plainenglish.io/uv-was-82-faster-than-pip-then-i-cleared-the-cache-and-it-was-1-9-f5e3e7ad92b1) (member-only blog; cold against warm timings, seen through search summary only)
  - [ROCm CLI pull request 170](https://github.com/ROCm/rocm-cli/pull/170) (issue report; hardlink falls back to copy across filesystems; seen through search summary only)
- **Limits:** One page fetch and one standard search. No source gives how fast a cache grows, measures the saving from a same-drive cache, or measures the cost of repeated purging on a machine like this one (the cold-cache timings are single runs on other machines; a local before/after measurement would settle it). The Windows hard-link behaviour (does deleting the cache copy free space while environments still link to it) was not tested here. Link-mode details vary by uv version; check `uv --help` and the docs for the installed version.
- **Checked:** 2026-11-23 (first check 2026-11-15; cold-cache cost added 2026-11-23)
