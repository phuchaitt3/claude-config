---
name: docker
description: Load before building images, pruning, bringing up a Compose stack, or when the system drive or Docker's disk is low ("disk full", "I/O error" in a build, Docker or Ollama failing to start). How to check Docker's disk use, what is safe to prune, how to give space back on Windows (WSL 2), and what an agent never does without the user's yes.
---

# Docker disk space

Added 2026-11-01 after a Docker data disk grew to 49 GB on a laptop's system drive and filled it, which broke image builds and local models. (standard: standards/docker-disk, checked 2026-11-01)

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
