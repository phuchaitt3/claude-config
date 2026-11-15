---
topic: cache-location-windows
area: Software process
question: Should every cache (developer tools, apps such as a browser or music player) move to a second drive, and is that standard practice?
checked: 2026-11-15
review_months: 12
status: current
---
# Where developer and app caches should live on a Windows machine with a small system drive

- **Question:** Should every cache (developer tools, apps such as a browser or music player) be moved to a second drive, and is that standard practice?
- **Finding:**
  - **Developer caches: yes, move them, and keep each beside the projects that use it.** Microsoft's Dev Drive documentation says a developer drive is for source repositories, package caches and build output, and gives a variable per tool to redirect the cache: `npm_config_cache` (npm), `PIP_CACHE_DIR` (pip), `NUGET_PACKAGES` (NuGet), `VCPKG_DEFAULT_BINARY_CACHE`, `CARGO_HOME`, `GRADLE_USER_HOME`, `MAVEN_OPTS`. It says the old folder's contents can be moved over, and that package caches can be regenerated, so they need no backup. Hugging Face documents `HF_HOME` or `HF_HUB_CACHE`; uv documents `UV_CACHE_DIR`. The reason to keep the cache with the projects is that uv links files from its cache into environments and falls back to slower copies across filesystems (see `uv-cache-management`).
  - **Not everything moves.** The same Microsoft page says developer tools and SDKs belong on the system drive and not on a Dev Drive, and that applications should not be installed there; a Dev Drive cannot be the C: drive and is meant for build and project files. A second ordinary drive is not a Dev Drive, but the split it describes (tools on C:, project data and caches elsewhere) is the same.
  - **Setting a variable does not move the old cache,** and a running program keeps the environment it started with: a process started before the variable was set (an editor, its terminals and chats) still uses the old default until restarted. Windows' docs say to restart open console windows or reboot after changing a variable. *Observed here:* the variable was set at user level on 2026-11-13, yet 9.3 GB of uv cache kept growing on C: until 2026-11-15, because the processes using it predated the variable.
  - **Consumer apps (browser, music player): do not relocate by default.** Their caches are small to moderate, self-managing, and the moves are unsupported or fragile. Spotify's community staff say the cache folder cannot be changed on desktop (only the downloaded-songs location in settings); a directory junction is the common workaround, with reports that Spotify keeps writing to C: or that updates change the location. For Edge, no source was found; clear its cache from the browser's settings (Settings > Privacy > Clear browsing data) when space is short. *Checker's inference:* clearing is the right tool for app caches, because they rebuild themselves and are not shared across projects.
  - **Rule of thumb (checker's inference from the sources):** move caches that a tool lets you configure with an officially documented variable or setting and that grow with project work (package managers, model hubs); clear, do not move, caches an app manages itself; never junction an app's data folder unless the app's own docs allow it.
  - **Docker Desktop's disk file is its own case:** see `docker-disk`.
- **Evidence strength:** *official standard* (Microsoft Dev Drive docs, Hugging Face docs, uv docs) for the variables and the tools-stay-on-C: advice; *anecdotal* (Spotify forum and guide posts) for the app-cache points; the rule of thumb is the checker's own inference.
- **Sources:**
  - [Microsoft Learn, Set up a Dev Drive on Windows 11](https://learn.microsoft.com/en-us/windows/dev-drive/) (official docs; package-cache variables, what to put on the drive, what not to)
  - [Hugging Face, understand caching](https://huggingface.co/docs/huggingface_hub/guides/manage-cache) (official docs; `HF_HOME`, `HF_HUB_CACHE`, symlink limits on Windows, cache cleaning commands)
  - [uv docs, caching](https://docs.astral.sh/uv/concepts/cache/) (official docs; `UV_CACHE_DIR`, same-filesystem advice)
  - [Spotify community, changing the cache location](https://community.spotify.com/t5/Desktop-Windows/Cache-setting-still-going-to-OS-drive/m-p/1184395) (vendor forum; cache folder not configurable, junction reports)
- **Limits:** Two standard searches and two page fetches. No source covers Edge or Chromium cache relocation (the `--disk-cache-dir` flag was not found documented); no measurement of the speed difference between caches on the system SSD and a second drive, which may be slower (a hard disk is slower than an SSD for many small files). pnpm's store-beside-projects rule was not checked here.
- **Checked:** 2026-11-15
