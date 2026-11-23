---
topic: laptop-vs-pc-benchmark
area: Agent setup
question: How do the user's laptop (GTX 1660 Ti) and desktop PC (i3-8100, GTX 1060 6 GB) compare on one identical set of small jobs, and where should heavy local jobs run?
checked: 2026-11-23
review_months: 6
status: current
---

# Laptop vs PC on one identical job set

Own measurement, not an industry practice (three laptop and two PC runs of the test job, one run per machine for the other jobs; one afternoon, 2026-11-23). Job script: `scripts/bench_machine.py` at commit d14531e, each job under its machine's own `gpu_run.py` lock. Both machines idle, GPU clock cap off on the laptop.

| Job | Laptop | PC | PC time ÷ laptop time |
|---|---|---|---|
| Config-repo test suite (766 tests) | 142.1, 140.3, 146.9 s (mean 143.1) | 92.0 s and 96.3 s | 0.66 (PC faster) |
| Load: 2 GB float32 build, sort, five 2048x2048 matrix products | 51.6 s, 2.1 GB peak | 56.7 s, 2.07 GB peak | 1.10 |
| GPU: 60 s fp32 2048x2048 matrix products | 4.47 and 4.42 TFLOPS, 47 to 70 C | 3.24 and 3.32 TFLOPS, 49 to 75 C | 1.36 (0.74x throughput) |
| GPU: ResNet-50 training, batch 32, fp32, 90 s (random weights, synthetic images) | 105.2, 104.8, 104.7 img/s, peak 71 C, 2.92 GB GPU memory | 72.3, 72.0, 70.0 img/s, peak 79 C, 2.85 GB GPU memory | 1.47 (0.68x throughput) |

**Machines:** laptop Python 3.12.3 (conda), torch 2.5.1+cu121; PC Python 3.12.9 in a scratch env, torch 2.5.1+cu121, i3-8100 (4 cores), 15.9 GB RAM with 7.5 GB free before the runs.

**Reading (inference from these numbers only):**
- Test suites and other CPU work: the PC was not slower; it was faster on this suite. Peak RAM of the tests was 0.15-0.21 GB, so memory was not the limit.
- RAM-heavy loads: about equal (10% slower on the PC).
- GPU compute: the PC's card gave 68-74% of the laptop's throughput on both GPU jobs, ran 5-8 C hotter, and neither machine showed thermal slowdown (median SM clock about 1665-1695 MHz laptop, 1885-1911 MHz PC), so the gap is the card, not throttling. The laptop's clock cap was off; with the cap on (about 15% slower, per the gpu-cap skill) the laptop would be near the PC.
- The ResNet-50 job uses a real architecture but random weights and synthetic images: it says nothing about data loading, transformers, mixed precision (neither card has tensor cores in fp32 use here), or runs longer than 90 s. The PC's later runs started warm (56, 69, 71 C).

**Setup notes that cost time:** the first PC run had 5 failed tests, from a missing PyYAML in the scratch env, not from the PC. `uv pip install --extra-index-url ... --index-url ...` put PyPI first and installed CPU-only torch; install `torch==2.5.1+cu121` from the PyTorch index only. The PC has no `.wslconfig`, so Docker's WSL2 uses the default of 50% of RAM (about 8 GB). `test_gpu_run.py` passed (39 tests) on the PC under Python 3.14.0 and 3.12.9.

**Limits:** small sample, one pair of machines, one run per machine for the load and GPU jobs, no battery or cap states, no long-run heat.

**Checked:** 2026-11-23
