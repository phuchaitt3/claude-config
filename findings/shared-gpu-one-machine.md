# Sharing one GPU machine between several users or agents

- **Question:** How do teams share one GPU machine between several users (or agent chats) so that jobs do not collide, and how do they know afterwards that it was shared properly?
- **Checked:** 2026-11-12

## Finding

The established pattern has three parts. A lock alone is only the first.

1. **A scheduler or queue, not ad-hoc starts.** Users submit jobs and the scheduler gives out the GPU when it is free, or queues the job (NVIDIA DGX best practices: Slurm, with whole-node "exclusive access" or GPUs as a consumable resource). On a single small server the same idea comes as a light queue: GPU Task Spooler (`ts`, "SLURM for small individual servers"), `gq` (a single-user GPU scheduler for one Linux workstation), `gpuq`. Several jobs on one GPU without isolation is discouraged: Slurm users note MPS is for one user's jobs, and a paper warns that processes sharing a GPU have no isolation.
2. **Enforcement: jobs cannot use the GPU outside the scheduler.** NVIDIA's DeepOps guidance hides the GPUs from plain login sessions because "we want to avoid having users run a compute task on the GPUs without a Slurm job". The mechanism is the OS (cgroups) or the driver: NVIDIA compute mode `EXCLUSIVE_PROCESS` allows one CUDA context per device. Both are Linux or datacenter features. Compute mode resets to DEFAULT after a reboot, and on Windows a GeForce card runs the WDDM driver model, where setting compute mode appears not to be supported (indirect evidence: NVML returns "not supported" under WDDM, per an NVIDIA forum; not confirmed by NVIDIA docs).
3. **Accounting and monitoring that run all the time.** Slurm's GPU scheduling requires job accounting. DCGM keeps per-process and per-job GPU statistics (`dcgmi stats --pid/--job`) as a daemon. Lighter tools sample to a log: `nvidia-smi dmon`/`pmon`, `--query-compute-apps`, `gpustat`. Sampling can miss short processes, and process attribution is unreliable with MPS or containers.

**Checker's inference for a Windows laptop shared by agent chats:** part 1 is available (a lock-and-queue wrapper). Part 2 is not: no cgroups, no Slurm, and compute mode is likely unsupported under WDDM (tested on one GeForce laptop: `driver_model.current` WDDM, `compute_mode` Default, and `--query-compute-apps` listed no processes while idle). So the substitute for enforcement is part 3 done continuously: a monitor that runs whether or not anyone is at the machine (a scheduled task), and flags GPU use while no job holds the lock. Checking only when someone happens to look (for example on each chat prompt) leaves gaps exactly when unattended jobs run.

## Sources

- [NVIDIA DGX best practices: managing resources](https://docs.nvidia.com/dgx/bp-dgx/resources.html) (official docs; Slurm, exclusive access, accounting).
- [NVIDIA blog: deploying a multi-user cluster on DGX (DeepOps)](https://developer.nvidia.com/blog/deploying-rich-cluster-api-on-dgx-for-multi-user-sharing) (vendor blog; hide GPUs from non-Slurm sessions).
- [slurm-users: sharing a GPU](https://lists.schedmd.com/pipermail/slurm-users/2022-April/008570.html) (community mailing list; MPS is per user).
- [GPU sharing isolation, arXiv 2410.22254](https://export.arxiv.org/pdf/2410.22254) (academic).
- [GPU Task Spooler](https://github.com/justanhduc/task-spooler) and [gq](https://pypi.org/project/gq-local) (community tools).
- [nvidia-smi documentation](https://docs.nvidia.com/deploy/nvidia-smi) (official; compute modes, reset on reboot, GOM and WDDM) and [NVIDIA forum: compute mode not supported under WDDM](https://forums.developer.nvidia.com/t/how-can-i-tell-whether-an-exclusive-process-mode-gpu-is-taken-or-not/273706) (community).
- [DCGM process and job statistics](https://docs.nvidia.com/datacenter/dcgm/latest/learn/core-services/process-and-job-statistics.html) (official docs).

## Limits

The sources are about Linux servers and clusters with several human users; none covers a Windows laptop shared by AI agents, so the "substitute for enforcement" is the checker's inference. Read partly through search summaries. Compute mode under WDDM was not tested by setting it (that needs admin rights and changes the machine). No source gives a monitoring interval; 5 minutes is a default under test.
