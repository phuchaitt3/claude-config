---
topic: notes-repo-autosync-trigger
area: Software process
question: To keep a small notes repository in sync between two machines through git, should the sync run on a fixed timer, on file changes, or on events (session start and end, wake from sleep), and how often is a timer worth running?
checked: 2026-11-23
review_months: 12
status: current
---

- **Question:** Is a fixed 3-minute scheduled sync (commit, pull, push) a sound design for two machines, or should it be triggered by activity?
- **Finding:**
  - Existing auto-sync tools mix triggers rather than choosing one. git-auto-sync watches the filesystem, also polls every 10 minutes, and syncs when the machine resumes from suspend. git-sync-rs has a watch mode with a debounce option and an optional periodic interval (5 minutes in its example). git-repo-watch is poll-only with a default of one hour. Obsidian sync plugins pull on app open or when the app regains focus, with an optional every-N-minutes timer; the plugin defaults found are 0 (off) or 30 s fetch. (sourced)
  - Git's own background maintenance, which prefetches from remotes, runs hourly by default. (sourced)
  - Hooks that fire on a local commit cannot see the other machine's work, so they cover the push side only. (inference)
  - A timer on a laptop wakes the network each run even when nothing changed; a watcher with debounce costs almost nothing idle. (inference, not measured)
  - Sensible design: event triggers (session start, session end, resume, a debounced file watch) as the main path, plus a slow safety-net timer (about 10-15 minutes) for edits made outside those events. (inference from the above)
- **Evidence strength:** *anecdotal* (tool READMEs and plugin listings; no benchmark of battery or CPU cost found).
- **Sources:**
  - [git-auto-sync](https://github.com/GitJournal/git-auto-sync) (tool README: filesystem watch, 10-minute poll, resume trigger)
  - [git-sync-rs](https://docs.rs/crate/git-sync-rs/0.7.6/source/README.md) (tool docs: watch mode, debounce, interval)
  - [git-repo-watch](https://npmjs.com/package/git-repo-watch) (package listing: poll default one hour)
  - [git maintenance](https://git-scm.com/docs/git-maintenance) (official docs: hourly prefetch schedule)
  - [Simple Git Sync](https://community.obsidian.md/plugins/simple-git-sync), [Git Commands](https://community.obsidian.md/plugins/git-commands), [Smart Git Sync](https://community.obsidian.md/plugins/lkmavi-smart-git-sync) (Obsidian plugin listings: intervals and defaults)
- **Limits:** one search round; no source measured the CPU, network or battery cost of a 3-minute timer; no source covered gitwatch or Windows Task Scheduler specifics. The cost points are the checker's reasoning.
- **Checked:** 2026-11-23
