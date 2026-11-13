# Sharing one GPU machine between several users or agents

- **Question:** How do teams share one GPU machine between several users (or agent chats) so that jobs do not collide, and how do they know afterwards that it was shared properly?
- **Checked:** 2026-11-12; long-running services section added 2026-11-13
- **Evidence strength:** *official standard* for the scheduler, allocation and Ollama facts (NVIDIA, Slurm, Kubernetes, Docker and Ollama docs); *common practice* for owner labels; the laptop designs are the checker's inference.

## Finding

The established pattern has three parts. A lock alone is only the first.

1. **A scheduler or queue, not ad-hoc starts.** Users submit jobs and the scheduler gives out the GPU when it is free, or queues the job (NVIDIA DGX best practices: Slurm, with whole-node "exclusive access" or GPUs as a consumable resource). On a single small server the same idea comes as a light queue: GPU Task Spooler (`ts`, "SLURM for small individual servers"), `gq` (a single-user GPU scheduler for one Linux workstation), `gpuq`. Several jobs on one GPU without isolation is discouraged: Slurm users note MPS is for one user's jobs, and a paper warns that processes sharing a GPU have no isolation.
2. **Enforcement: jobs cannot use the GPU outside the scheduler.** NVIDIA's DeepOps guidance hides the GPUs from plain login sessions because "we want to avoid having users run a compute task on the GPUs without a Slurm job". The mechanism is the OS (cgroups) or the driver: NVIDIA compute mode `EXCLUSIVE_PROCESS` allows one CUDA context per device. Both are Linux or datacenter features. Compute mode resets to DEFAULT after a reboot, and on Windows a GeForce card runs the WDDM driver model, where setting compute mode appears not to be supported (indirect evidence: NVML returns "not supported" under WDDM, per an NVIDIA forum; not confirmed by NVIDIA docs).
3. **Accounting and monitoring that run all the time.** Slurm's GPU scheduling requires job accounting. DCGM keeps per-process and per-job GPU statistics (`dcgmi stats --pid/--job`) as a daemon. Lighter tools sample to a log: `nvidia-smi dmon`/`pmon`, `--query-compute-apps`, `gpustat`. Sampling can miss short processes, and process attribution is unreliable with MPS or containers.

**Checker's inference for a Windows laptop shared by agent chats:** part 1 is available (a lock-and-queue wrapper). Part 2 is not: no cgroups, no Slurm, and compute mode is likely unsupported under WDDM (tested on one GeForce laptop: `driver_model.current` WDDM, `compute_mode` Default, and `--query-compute-apps` listed no processes while idle). So the substitute for enforcement is part 3 done continuously: a monitor that runs whether or not anyone is at the machine (a scheduled task), and flags GPU use while no job holds the lock. Checking only when someone happens to look (for example on each chat prompt) leaves gaps exactly when unattended jobs run.

## Long-running GPU services (added 2026-11-13)

A model server (an inference container, Ollama) is not a job that ends: it holds GPU memory from start until it is stopped, and often sits idle.

1. **The allocation lasts as long as the holder, not as long as the start command.** In Kubernetes, the classic device plugin gives a container a whole GPU for the container's lifetime, and sharing one GPU between pods is an explicit opt-in (time-slicing, MPS, MIG, or Dynamic Resource Allocation claims). Slurm likewise holds a job's GPUs until the job ends, including a server run inside the job. A lock taken around `docker run -d` or `docker compose up -d` is released within seconds while the container keeps the GPU, so the lock has to be tied to the container's life (checker's inference from the two models above).
2. **Ollama is a GPU service that loads on demand.** Per its FAQ: a model stays loaded for 5 minutes after its last request; `keep_alive: 0` unloads it right after a response and `ollama stop <model>` unloads it at once; `OLLAMA_MAX_LOADED_MODELS` defaults to 3 per GPU; when memory is short, new requests queue until the model can load, and a model can be split between GPU and system RAM (`ollama ps` shows the split). On Windows it reads the user's environment variables, set before Ollama starts. So Ollama can take GPU memory at any time, whoever holds a lock; on a shared machine the levers are a short keep-alive, a low model cap, and `ollama stop` before a heavy job.
3. **Every container should carry its owner.** Compose labels its containers by project (`com.docker.compose.project`), and `--remove-orphans` and label filters (`docker ps --filter label=...`) touch only that project's containers. Guides recommend namespaced owner labels (`com.example.owner`) applied when the container is created, and filtering by label before removing anything. An unnamed `docker run --rm` with no label cannot be traced to the person or task that started it. Evidence: blog guides plus Compose's own behaviour; no official Docker statement of practice.
4. **Memory caps sit at two levels.** Compose `deploy.resources.limits.memory` (or `mem_limit`) caps one container, and GPU access is reserved per service with `deploy.resources.reservations.devices` (official Docker docs). On Windows, `%UserProfile%\.wslconfig` caps the whole WSL 2 VM; a newer, experimental `autoMemoryReclaim=gradual` gives memory the VM has freed back to Windows. Without it, Windows can show RAM still in use after containers stop (blog guide; experimental flag).

**Checker's inference for a Windows laptop shared by agent chats:** treat a GPU service as a job whose end is the container's stop. Hold the lock for the container's life: a wrapper that starts it and waits on `docker wait`, or a lock record naming the container that `check` treats as the holder while that container runs. Label each GPU container with the chat and task that started it. Count Ollama's `llama-server` as a known user, and unload it before a heavy job. Since this platform has no OS-level enforcement (part 2 above), a pre-command hook can refuse an unlabelled or unlocked GPU start (`findings/agent-permission-enforcement`).

Sources for this section:

- [NVIDIA DRA driver docs: GPU allocation](https://dra-driver-nvidia-gpu.sigs.k8s.io/docs/concepts/gpu-allocation/) (official docs), [NVIDIA GPU Operator: time-slicing](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html) (official docs), [CNCF: NVIDIA device plugin](https://www.cncf.io/blog/2024/04/30/accelerating-machine-learning-with-gpus-in-kubernetes-using-the-nvidia-device-plugin/) (foundation blog).
- [Ollama FAQ](https://docs.ollama.com/faq) (official docs; keep-alive, stop, model cap, queueing, Windows variables).
- [Docker Compose GPU support](https://docs.docker.com/compose/how-tos/gpu-support/) and [Compose deploy specification](https://docs.docker.com/reference/compose-file/deploy/) (official docs).
- [Docker labels for container management](https://oneuptime.com/blog/post/2026-01-25-docker-labels-container-management/view) and [Compose orphan containers](https://oneuptime.com/blog/post/2026-02-08-how-to-fix-docker-compose-orphan-container-warnings/view) (vendor blogs).
- [Docker Desktop memory limits on Windows](https://oneuptime.com/blog/post/2026-02-08-how-to-configure-docker-desktop-memory-and-cpu-limits-on-windows/view) (vendor blog; `.wslconfig`, `autoMemoryReclaim`).

Limits of this section: no source covers locking a long-running service on one workstation without a cluster scheduler; the hold-for-life design is inferred from Kubernetes and Slurm semantics. The label and `autoMemoryReclaim` points rest on blog guides. Ollama behaviour is as of the FAQ read on 2026-11-13 and changes between versions.

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
