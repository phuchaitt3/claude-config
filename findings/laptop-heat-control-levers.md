---
topic: laptop-heat-control-levers
area: Software process
question: To keep a laptop running long unattended GPU jobs cooler, is "wait to cool before a job starts" a standard practice, and how does it compare with capping GPU power?
checked: 2026-11-17
review_months: 12
status: current
---
# Levers for keeping a laptop cooler under long GPU jobs

- **Question:** To keep a laptop running long unattended GPU jobs cooler, is "wait to cool before a job starts" (take the job lock only below a temperature) a standard practice, and how does it compare with capping the GPU's power?
- **Checked:** 2026-11-17
- **Evidence strength:** *anecdotal* for volunteer-computing practice and power-cap trade-offs (forum posts, blogs); *peer-reviewed or patent* only for thermal-aware scheduling in general, which does not describe this exact rule.

## Finding

- **Wait-to-cool is not an established standard.** No HPC batch scheduler or published practice was found that holds a job's start until the node is below a temperature. Research on thermal-aware scheduling regulates running work with DVFS (lower clocks) under a temperature cap instead of delaying starts (Chrobak et al.; Stolf, Sun & Pierson 2017). Patents on temperature-aware task scheduling describe admission control (accept a task only if its projected heat keeps units under a threshold), the nearest thing, but they are patents, not practice.
- **Volunteer computing (BOINC) is the closest real-world analogue, and it uses third-party tools.** BOINC has no built-in temperature pause. Users run TThrottle (Windows) to hold CPU and GPU near a set temperature, or boinc-gpucontrol, which suspends the GPU at a target temperature and resumes it once cool. Forum users note that BOINC's CPU-usage throttle does not cool the GPU, and that suspending work mid-task is how these tools act: that adds heat-cool cycles.
- **Capping GPU power is the more common first lever.** Guides and forum users recommend `nvidia-smi -pl <W>` first and an undervolt only if still too hot, since an aggressive undervolt can make an unattended machine unstable. Reported costs are small: about 6% throughput for 25% less power (RTX 5090), about 2% for 30% less (GB10); single-user reports, not controlled tests. The limit can reset at reboot, so it is reapplied at start-up. On laptops, check which limiter is active first (`nvidia-smi -q -d PERFORMANCE`: SW power cap vs thermal) and benchmark under sustained load, not bursts.
- **Checker's synthesis:** a power cap lowers the average temperature and fan noise for the whole run with a small, measurable speed cost. Wait-to-cool lowers only the start temperature: once a job runs, it heats up to the same level, and gaps between jobs add heat-cool cycles, which `laptop-thermal-tiers` lists as a wear driver. Wait-to-cool is a fit only as a guard against starting a job on an already hot machine (for example after a daytime load), not as the main heat control.

## Sources

- [Chrobak et al.: Algorithms for temperature-aware task scheduling in microprocessor systems (arXiv 0801.4238)](https://arxiv.org/abs/0801.4238) (peer-reviewed theory).
- [USPTO 10133610: temperature-aware task scheduling](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10133610) (patent).
- [Einstein@Home forum: automating GPU suspend for summer heat](https://einsteinathome.org/goto/comment/198804) (forum).
- [boinc-gpucontrol (SourceForge)](https://sourceforge.net/p/boinc-gpucontrol/code) (third-party tool).
- [boinctools (GitHub)](https://github.com/LucoDevro/boinctools) (third-party scripts; fixed-interval pauses).
- [GPUGRID forum: limiting GPU clock and temperature automatically](https://gpugrid.net/gpugrid/forum_thread.php?id=4815) (forum).
- [Undervolting a GPU for a 24/7 local agent](https://openclawdc.com/blog/undervolt-gpu-24-7-local-agent/) (blog guide).
- [NVIDIA forum: cooler GB10 temps, almost no performance lost](https://forums.developer.nvidia.com/t/cooler-gb10-temps-almost-no-performance-lost/372662) (vendor forum, user report).
- [NVIDIA forum: RTX 3050 Mobile SW power cap during PyTorch compute](https://forums.developer.nvidia.com/t/rtx-3050-mobile-vram-stuck-at-810-mhz-p5-state-sw-power-cap-during-pytorch-compute-comfyui/382741) (vendor forum).

## Limits

No controlled study of either lever on laptops was found. The power-cap costs come from desktop and workstation cards; a laptop GPU's cost at a given cap has to be measured on the machine. The search did not cover Slurm power-capping plugins in depth.
