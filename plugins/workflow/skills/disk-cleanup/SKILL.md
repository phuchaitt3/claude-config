---
name: disk-cleanup
description: Load before measuring or freeing space on a full or low drive ("disk full", "free up C:", "what is using my disk", a low-disk hook warning). Fast measuring with WizTree, what to clean first, and what never to delete. Docker's own disk file is `workflow:docker`.
---

# Freeing disk space

Added 2026-11-15 (user's decision) after a chat walked a 238 GB drive with a PowerShell loop for over 15 minutes, where an MFT-reading analyzer takes seconds. (standard: findings/disk-cleanup-windows, checked 2026-11-15)

1. **Measure, never walk.** Never scan a whole drive with `Get-ChildItem -Recurse`, `du` or a folder loop: it takes minutes and slows every chat. Run `schtasks /Run /TN WizTreeExport`, wait until `$env:ProgramData\WizTreeExport\C.csv` has a new write time, and read its top 15 rows (sorted by size; folder rows end in `\`). If the task does not exist, ask the user to run WizTree themselves, or to run `~/claude-config/scripts/wiztree_task_setup.ps1 -Source <WizTree folder>` once in an administrator PowerShell, which sets the task up so no later run needs a prompt.
2. **Report** the top items to the user: size, what each is, and its group: Windows, developer caches, Docker, user data. Windows first: Settings > System > Storage > Cleanup recommendations; `Dism /Online /Cleanup-Image /AnalyzeComponentStore` says whether a component cleanup is worth it.
3. **Delete nothing without the user's yes for that item.** Clean a cache with its own command (`uv cache prune`, `pip cache purge`, `pnpm store prune`, `npm cache verify`), never by deleting its folder; Hugging Face models one folder at a time. Docker goes through `workflow:docker`. Never: Docker volumes, credential files, anything not identified, `DISM /ResetBase` (it makes installed updates impossible to uninstall).
4. **Log the outcome** (date, what was removed, GB freed, free space after) where the user keeps machine notes, so the next cleanup starts from it.
