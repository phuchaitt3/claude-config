---
name: docker
description: Load before building images, pruning, fetching a tool or model server (where tools come from), bringing up a Compose stack, or when Docker's own disk is low or failing ("I/O error" in a build, Docker or Ollama failing to start). How to check Docker's disk use, what is safe to prune, how to give space back on Windows (WSL 2), and what an agent never does without the user's yes. A whole drive running low (finding what takes the space): `workflow:disk-cleanup`.
---

# Docker: where tools come from, and disk space

## Where tools and servers come from (user's decision, 2026-11-17)

An agent gets a tool or server from an official or digest-pinned Docker image or from a package manager (pip, uv, npm, winget); it never downloads a loose binary or archive and runs it. Why: Claude Code's auto-mode check refuses to run an unpacked download, so an overnight run stalled for two days on a llama.cpp server (book-rag-app #245), and an allow rule per download does not scale. A container fits the stack: Compose, `gpu_run.py hold` for a GPU service, and the Docker cleanup hook. Example: the llama.cpp server runs as `ghcr.io/ggml-org/llama.cpp:server-cuda` with the GGUF folder mounted. Model weights (GGUF, safetensors) are data, not programs: download them with the tool's own fetcher or a pinned URL, check the size and a published SHA-256 where there is one, and keep them outside the repository. A tool with no image or package route becomes a `needs-you` item naming the exact download and its checksum; the agent adds no permission rule to `settings.json` itself.

# Docker disk space

Added 2026-11-01 after a Docker data disk grew to 49 GB on a laptop's system drive and filled it, which broke image builds and local models. (standard: findings/docker-disk, checked 2026-11-01)

## Before heavy Docker work

1. Check free space on the system drive and the size of Docker's data disk file (on Windows with WSL 2: `docker_data.vhdx` under `%LOCALAPPDATA%\Docker\wsl\disk`). Run `docker system df`.
2. If free space is under about 10 GB, prune and compact before building.
3. A full drive: scan the whole drive top-down before calling any space "unaccounted".

## Safe without asking

- `docker system df`, `docker builder prune -f` (optionally `--filter until=72h` or `--keep-storage 5GB`), `docker image prune` (dangling only).

## Ask the user first

- Anything that removes volumes (`--volumes`, `docker volume rm`, `docker system prune -a`) or resets Docker's data: volumes hold the user's data, such as a local database.
- Compacting the data disk (below): Docker is down for a few minutes and Windows shows one admin prompt.

## Giving space back (Windows, WSL 2)

The disk file never shrinks by itself. Prune first (compacting before pruning reclaims nothing), quit Docker Desktop, `wsl --shutdown`, then run diskpart elevated with a script of: `select vdisk file="<path>"`, `attach vdisk readonly`, `compact vdisk`, `detach vdisk`, `exit`. (`Optimize-VHD` needs Hyper-V, which Windows Home lacks.) Report the size before and after. Start Docker Desktop again afterwards.

## Keeping it small

- Prune build cache after build-heavy sessions.
- Docker's disk limit and disk location settings are documented for the Hyper-V backend only; on WSL 2 do not promise the user a cap there.
- Do not turn on WSL sparse VHD: it was reported gated for data-corruption risk and breaks `Optimize-VHD`.
