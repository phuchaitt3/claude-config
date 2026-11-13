# Docker disk space on Windows (WSL 2)

- **Question:** How do teams keep Docker Desktop's disk use under control on Windows with the WSL 2 backend, and how is the space given back?
- **Checked:** 2026-11-01

## Finding

- Docker Desktop's WSL 2 data lives in a virtual disk file (`.vhdx`) on the system drive. Deleting images, cache or volumes frees space inside the file but the file on Windows does not shrink; it only grows (several community write-ups agree).
- The usual way to give the space back: prune first (compacting before pruning reclaims nothing), quit Docker Desktop, run `wsl --shutdown`, then compact the file with `Optimize-VHD -Mode Full` (needs Hyper-V) or, on Windows Home, `diskpart` (`select vdisk file=...`, `attach vdisk readonly`, `compact vdisk`, `detach vdisk`). The write-ups report large savings (for example 145 GB to 52 GB).
- Pruning: `docker system df` shows usage by category (before and after a prune); `docker builder prune` removes unused build cache, `--keep-storage` caps the cache size, `-a` also removes cache in use; the prune commands accept `--filter until=<duration>`. Volumes are only removed with `--volumes`, which deletes data.
- Docker's settings page (official docs) lists "Disk usage limit" and "Disk image location" for the **Hyper-V** backend only, not WSL 2. So a size cap or relocation through Docker Desktop settings is not confirmed for a WSL 2 machine.
- WSL's sparse virtual disk (`[experimental] sparseVhd` in `.wslconfig`, `wsl --manage <distro> --set-sparse true`) is meant to shrink the disk automatically, but sources report it was gated or disabled in a WSL release because of possible data corruption, and `Optimize-VHD` fails on a sparse disk. Not a safe default.
- Checker's inference (not stated by the sources): on a WSL 2 machine the dependable controls are regular builder pruning and a compaction when free space on the system drive gets low.

## Sources

- [Reclaim disk space by compacting the Docker Desktop WSL 2 VM](https://nickjanetakis.com/blog/reclaiming-tons-of-diskspace-by-compacting-your-docker-desktop-wsl-2-vm) (community blog).
- [Docker on Windows eating your C drive](https://dev.to/hamada147/docker-on-windows-eating-your-c-drive-how-i-reclaimed-over-350gb-from-bloated-vhdx-files-11dm) and [chasing missing disk space](https://dev.to/ryansgi/docker-windows-chasing-missing-disk-space-2b0k) (community posts).
- [Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/) (official docs; disk limit and image location listed for Hyper-V).
- [docker system prune](https://depot.dev/blog/docker-system-prune) (vendor blog), [docker builder prune](https://oneuptime.com/blog/post/2026-02-08-how-to-use-docker-builder-prune-to-clean-build-cache/view) (vendor blog) and a [mirror of the system prune reference](https://docker-docs.uclv.cu/engine/reference/commandline/system_prune/) (mirror of official docs).
- [WSL sparse VHD thread](https://learn.microsoft.com/en-us/answers/a/1444303) (Microsoft Q&A, community answer) and [Managing WSL disk space](https://dev.to/octasoft-ltd/managing-wsl-disk-space-fm9) (community post).

## Limits

No official Docker page on compacting the WSL 2 disk was found; the procedure rests on community write-ups, and one of them reports the file growing again after updates. The prune details come from vendor blogs and a mirror, not docs.docker.com. The sparse-disk status is not confirmed against Microsoft's WSL documentation and may have changed. The Docker settings page was read once; a newer Docker Desktop may add a WSL 2 limit.
