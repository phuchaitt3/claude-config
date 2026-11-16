---
topic: memory-admission-one-machine
area: Agent setup
question: How do schedulers decide whether a job fits in memory before starting it on one machine (a lock versus a memory budget), how do they cover long-running services, and how is a VM or container memory cap sized?
checked: 2026-11-17
review_months: 12
status: current
---
# Memory admission on one shared machine

- **Question:** When several agents share one machine, is "one heavy job at a time" (a mutex) the standard, or do schedulers admit jobs against a memory budget? How do they treat services that keep running, and how is a VM or container memory cap (WSL 2, Compose) sized?

- **Finding:**
  - **Schedulers admit against memory, not only a slot count.** Slurm will not start a job whose memory request exceeds what the node offers (HPC site guide; default 1 GB per core when no request is given), and AWS ParallelCluster's memory-based scheduling co-locates jobs while protecting each one's requested memory. HTCondor matches a job only to a slot with `Memory` at least the job's `request_memory`; holding a job that later uses more is a site policy the admin writes (for example `MemoryUsage > RequestMemory`), not a default. LSF reserves memory as it frees up for a large pending job so small jobs do not starve it.
  - **Requests, not observed free memory, are the usual basis, and that is a known gap.** Slurm users ask for dispatch on actual free memory and do not get it by default. Kubernetes schedules on requests, and its docs say the scheduler should not place pods that would immediately push the node into eviction. A research arbitrator (Laminar, arXiv 2602.13789) samples the real memory watermark and pauses admission under pressure, which is the observed-memory variant; it is a preprint, not a deployed standard.
  - **A floor of free memory is kept for the system.** Kubernetes evicts when `memory.available` falls below 100 MiB on Linux and 500 MiB on Windows by default, and its own example reserves `systemReserved` = 10% of memory plus the eviction threshold (1.5 GiB on its example node). On Windows nodes `memory.available` is computed from commit (`CommitLimit - CommitTotal`), not free physical RAM, and the docs warn that the commit limit moves with page-file size.
  - **Single-workstation GPU queues use a free-memory threshold, not per-job requests.** The GPU fork of Task Spooler treats a GPU as free when more than 90% of its memory is free (`--set_gpu_free_perc`) and waits 30 s after each launch so the last job's memory shows up before the next check. Other small queues (Tasque, qgpu) are also memory-threshold based. None found takes a per-job memory estimate.
  - **Sizing a request or cap comes from measured peak plus a margin.** The Kubernetes Vertical Pod Autoscaler recommends a memory request from the 90th percentile of observed usage plus a 15% safety margin (`recommendation-margin-fraction` 0.15, upstream flags), over an 8-day decaying window; it sets requests, and limits are left to the operator as a safety net above that.
  - **WSL 2's VM defaults to 50% of Windows memory** (`memory` in `.wslconfig`; swap defaults to 25%), per Microsoft's docs. Microsoft gives no sizing method; its example uses 4 GB. Blog guides for a 16 GB host suggest 6-8 GB and leaving at least 4 GB for Windows; a Docker forum thread reports Docker Desktop exceeding the `.wslconfig` limit. Changes need a WSL shutdown or Docker Desktop restart.
  - **Long-running services hold resources for their life** (see `findings/shared-gpu-one-machine`, long-running services): the same reasoning applies to memory as to the GPU; a lock taken around `docker compose up -d` is released while the stack keeps its RAM.
  - **Checker's inference for this laptop (16 GB, Windows, several Claude sessions):** a mutex alone matches the small GPU queues but not the memory-aware schedulers; the standard pattern is admission against a memory figure with a reserve kept for the system, and on Windows that figure is commit headroom. Agent sessions are themselves memory users that no request covers (each about 0.5-0.65 GB measured here on 2026-11-17; 2-4 GB peak per sandboxed agent in `findings/agent-process-and-resource-control`), so the observed-memory variant (check free commit before granting a lock) fits better than per-job requests, which nobody here would keep accurate. A WSL cap is sized as measured peak of the stacks that run in it, plus 15%, bounded above by total RAM minus what Windows needs (sessions, editor, browser, a reserve).

- **Sources:**
  - Slurm memory requests, node limit and default (HPC site guide): https://supercomputing.tue.nl/documentation/kb/slurm/6/
  - Slurm memory-aware scheduling in AWS ParallelCluster (vendor blog): https://aws.amazon.com/blogs/hpc/slurm-based-memory-aware-scheduling-in-aws-parallelcluster-3-2
  - Slurm users asking to schedule on actual free memory (mailing list): https://groups.google.com/g/slurm-users/c/tpn7dev4GEU
  - LSF memory reservation for pending jobs (vendor docs, site mirror): https://www.hpc.dtu.dk/lsf931/lsf_admin/reserve_mem_pending_jobs.html
  - HTCondor matching on request_memory and hold policies (mailing list): https://www-auth.cs.wisc.edu/lists/htcondor-users/2025-May/msg00100.shtml and https://www-auth.cs.wisc.edu/lists/htcondor-users/2013-November/msg00090.shtml
  - Laminar, probe-first node-local admission (arXiv preprint): https://arxiv.org/pdf/2602.13789
  - Kubernetes node-pressure eviction: default thresholds, Windows commit signal, systemReserved example (official docs): https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/
  - Kubernetes: is available memory considered when scheduling (forum): https://discuss.kubernetes.io/t/is-available-memory-taken-into-consideration-when-scheduling-pods/28308
  - GPU Task Spooler, free-memory threshold and launch delay (project README): https://github.com/justanhduc/task-spooler
  - VPA recommender flags: percentile, 15% margin (upstream docs mirror): https://gitea.cncfstack.com/kubernetes/autoscaler/src/commit/037b3773550e96c42404c0777a41e99b669c8eb6/vertical-pod-autoscaler/docs/flags.md
  - VPA algorithm and decaying histogram (blog): https://ttanay.github.io/blog/vpa-algorithm
  - WSL `.wslconfig` memory and swap defaults (official docs, updated 2026-10-16): https://learn.microsoft.com/en-us/windows/wsl/wsl-config
  - Docker Desktop memory limits on Windows, 16 GB example (vendor blog): https://oneuptime.com/blog/post/2026-02-08-how-to-configure-docker-desktop-memory-and-cpu-limits-on-windows/view
  - Docker Desktop exceeding the `.wslconfig` limit (forum): https://forums.docker.com/t/docker-desktop-eats-ram-past-wsl-limit-set-in-wslconfig-file/128150

- **Limits:** No source covers agent chats sharing one Windows laptop; the admission design for it is the checker's inference from cluster schedulers. HTCondor evidence is mailing-list replies, not the manual. The Slurm default comes from one site's guide (sites configure it). The 6-8 GB WSL figures are blog advice, not Microsoft guidance. VPA flag defaults were read from a mirror of the upstream docs; third-party pages disagree on the percentile. Laminar is an unreviewed preprint. The per-session memory figure is one reading on this machine, not a benchmark.

- **Checked:** 2026-11-17
