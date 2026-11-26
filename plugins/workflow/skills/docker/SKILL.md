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
- When a task ends, remove its stack with `docker compose -p <project> down --rmi local`, which also removes the images it built (never `-v`) (user's decision, 2026-11-26).
- Docker's disk limit and disk location settings are documented for the Hyper-V backend only; on WSL 2 do not promise the user a cap there.
- Do not turn on WSL sparse VHD: it was reported gated for data-corruption risk and breaks `Optimize-VHD`.

## The WSL 2 memory cap (`~/.wslconfig`, `[wsl2] memory=`)

(User's decision, 2026-11-19, claude-config#19.) Docker Desktop's VM takes up to 50% of Windows memory unless capped; on this 16 GB laptop it is capped at **3 GB**. Basis: the book-rag-app Compose stack (db, qdrant, s3, migrate, api, worker, web; fake LLM and embedder) peaked at 1011 MB (`gpu_run.py hold` `end` event, `peak_stack_mem_mb`), plus about 0.5 GB for the VM's kernel and page cache and about 1.5 GB for the TEI reranker container or an image build. The cap limits RAM, not heat; for heat see `workflow:gpu-cap` and the thermal watchdog.

**PC (user's decision, 2026-11-23): no cap, default 50% of 15.9 GB (about 8 GB).** Measured on the PC with the book-rag-app stack (6 containers idle 0.79 GiB; WSL memory 3.97 GB; building the three images alone reached 6.05 GB; the database allows a 3 GB shared-memory area and a 2 GB index build). A 6 GB cap would have been tight for builds. The laptop's 3 GB cap stays; it is a laptop-sharing choice, not a rule for the PC. Measure again before capping the PC.

**Change it only with the user's yes**, in steps of 1 GB, and only when no Compose stack or GPU container runs (`docker ps`; `gpu_run.py check`): edit `memory=`, then `wsl --shutdown` (Docker Desktop restarts the VM on next use). The comment above the line in `~/.wslconfig` gets the date, the new value and the evidence.

**Signals that the cap is wrong:**

| Signal | Where | Meaning and step |
|---|---|---|
| A container exits with `OOMKilled=true` (`docker inspect <name> --format '{{.State.OOMKilled}}'`, `docker events --filter event=oom`) | Docker | cap too low: raise 1 GB |
| A Compose build or install dies with "Killed" or exit 137 | build output | cap too low: raise 1 GB, or build with fewer parallel jobs |
| `low_memory` rows (under 3 GB physical free) in `thermal.jsonl` while `docker stats` shows the stack near idle | `python ~/claude-config/scripts/night_timeline.py` | cap not the cause or too high: look at `top_mem_mb` first; lower 1 GB only if `vmmemWSL` is the top user |
| Harness kills ("was stopped because the system is running low on memory") | `night_timeline.py` | more headroom needed overall: check `top_mem_mb` for the biggest user before touching the cap |
| A new service in the stack (reranker, a bigger model server) or a much larger book | `gpu_run.py report --resource ram` (`peak_stack_mem_mb`) | re-measure with the new stack through `hold --resource ram`, then set the cap to the peak plus about 1.5 GB |

To measure: start the stack through `python ~/claude-config/scripts/gpu_run.py hold --resource ram --wait --purpose "<task> wsl peak" -- docker compose -p <name> up -d`, run a normal workload for several minutes, `docker compose -p <name> down` (never `-v`), then read `peak_stack_mem_mb`. The figure is the `docker stats` sum, a lower bound; it leaves out the VM's kernel and page cache, so never set the cap to it directly (the issue's first formula, peak x 1.15, gave 1.2 GB and was not applied). The 4 GB admission check in `gpu_run.py` still holds heavy jobs back when physical RAM is low, whatever the cap.
