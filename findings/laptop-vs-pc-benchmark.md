---
topic: laptop-vs-pc-benchmark
area: Agent setup
question: How do the user's laptop (GTX 1660 Ti) and desktop PC (i3-8100, GTX 1060 6 GB) compare on one identical set of small jobs, and where should heavy local jobs run?
checked: 2026-11-23
review_months: 6
status: current
---

# Laptop vs PC on one identical job set

Own measurement, not an industry practice (one run per laptop job, two to three per PC test job; one afternoon, 2026-11-23). Job script: `scripts/bench_machine.py` at commit d14531e, each job under its machine's own `gpu_run.py` lock. Both machines idle, GPU clock cap off on the laptop.

| Job | Laptop | PC | PC time ÷ laptop time |
|---|---|---|---|
| Config-repo test suite (766 tests) | 142.1 s (1 run) | 92.0 s and 96.3 s | 0.66 (PC faster) |
| Load: 2 GB float32 build, sort, five 2048x2048 matrix products | 51.6 s, 2.1 GB peak | 56.7 s, 2.07 GB peak | 1.10 |
| GPU: 60 s fp32 2048x2048 matrix products | 4.47 TFLOPS, 47 to 66 C | 3.24 TFLOPS, 49 to 71 C | 1.38 (0.73x throughput) |

**Machines:** laptop Python 3.12.3 (conda), torch 2.5.1+cu121; PC Python 3.12.9 in a scratch env, torch 2.5.1+cu121, i3-8100 (4 cores), 15.9 GB RAM with 7.5 GB free before the runs.

**Reading (inference from these numbers only):**
- Test suites and other CPU work: the PC was not slower; it was faster on this suite. Peak RAM of the tests was 0.15-0.21 GB, so memory was not the limit.
- RAM-heavy loads: about equal (10% slower on the PC).
- GPU compute: the PC's card gave about 73% of the laptop's throughput and ran 5 C hotter in 60 s. No thermal slowdown flag was checked, so the gap may include throttling.
- One short run per job and a synthetic matrix workload say nothing about real models, memory-bound GPU work or runs longer than the 60 s sampled.

**Setup notes that cost time:** the first PC run had 5 failed tests, from a missing PyYAML in the scratch env, not from the PC. `uv pip install --extra-index-url ... --index-url ...` put PyPI first and installed CPU-only torch; install `torch==2.5.1+cu121` from the PyTorch index only. The PC has no `.wslconfig`, so Docker's WSL2 uses the default of 50% of RAM (about 8 GB). `test_gpu_run.py` passed (39 tests) on the PC under Python 3.14.0 and 3.12.9.

**Limits:** small sample, one pair of machines, no run-to-run variance for the laptop, no battery or cap states, no long-run heat.

**Checked:** 2026-11-23
