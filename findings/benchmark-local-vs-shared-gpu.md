# Timing benchmarks on a personal machine versus a shared cloud GPU

- **Question:** Is a personal laptop a worse place to time a benchmark than a free shared cloud GPU (a Kaggle notebook), and what keeps a timing number trustworthy on either?
- **Checked:** 2026-11-12

## Finding

- **Neither place is trustworthy by default; no source ranks a laptop below a cloud GPU.** The sources agree on the controls, not on a winner. Cloud studies find large run-to-run spread on shared instances (CPU 10-20% between instances of one type, memory up to 270%, result spread from 0.03% to over 100% depending on benchmark and environment). GPU-specific figures come from vendor blogs: p99 latency 3-4x the median when a co-located tenant saturates shared resources. Laptop guidance names heat: a GPU that starts warm boosts to lower clocks, and consecutive runs on one system differ by a few percent.
- **A laptop's noise is under your control; a free shared cloud GPU's is not.** The laptop is one tenant you can quiet (no other GPU job, log temperature and clocks, cool down between runs). A Kaggle session gives no view of its neighbours or its clocks. That a hosted environment is isolated from your own other jobs is the checker's inference; Kaggle's isolation and clock behaviour were not checked.
- **Controls that recur across sources:** warm up to a stable state before measuring (one 2026 paper used six warm-up iterations, chosen because readings stayed within 3% over three runs); several repeated runs, reporting the median and the spread, not one number (MLPerf Training: 5 or 10 runs, drop fastest and slowest; this is training, not inference); log clocks, temperature and power, not only the score; interleave runs in time or run both variants side by side so that shared noise hits both (duet benchmarking: good for a ratio, gives no absolute number); greedy decoding for speed tests (one paper: temperature alone changed throughput by up to 21%).
- **A speed ratio from one machine is a result about that machine.** See [benchmark-setup-consistency](benchmark-setup-consistency.md): report the setup, and treat a second machine's ratio as a second data point.
- **Checker's inference for a shared laptop** (not stated by the sources): another job on the same GPU or RAM is a noise source of the same kind as a noisy neighbour, and larger than the few-percent thermal drift. A timing run on a shared laptop needs the GPU to itself, or the result is recorded as unreliable.

## Sources

- [Duet Benchmarking: Improving Measurement Accuracy in the Cloud, arXiv 2001.05811](https://arxiv.org/pdf/2001.05811) (academic).
- [Studying cloud performance variability for stream processing benchmarks, arXiv 2504.11826](https://arxiv.org/pdf/2504.11826) (academic).
- [MLPerf Training Benchmark, arXiv 1910.01500](https://arxiv.org/pdf/1910.01500) (industry consortium paper; run counts).
- [Pimp My LLM, arXiv 2602.17697](https://arxiv.org/pdf/2602.17697) (academic; warm-up of six iterations).
- [The Evolution of LLM Benchmarking in Production, 2605.24217](https://www.alphaxiv.org/overview/2605.24217) (preprint overview; temperature effect, client overhead).
- [UL Benchmarks support: scores vary between runs](https://support.benchmarks.ul.com/support/solutions/articles/44001791209-my-benchmark-score-seems-to-vary-wildly-between-runs) (vendor support; cooldown between runs, aimed at phones and tablets).
- [llenergymeasure, measurement warnings](https://henrycgbaker.github.io/llenergymeasure/explanation/methodology/measurement-warnings) (community tool docs; warm-up convergence as a validity check).
- [Noisy neighbor problem, GPU cloud](https://packet.ai/blog/noisy-neighbor-problem-gpu-cloud) and [bare metal vs virtualized GPU](https://www.spheron.network/blog/bare-metal-vs-virtualized-gpu-performance-consistency-benchmark/) (vendor blogs; indicative only).

## Limits

Read through search summaries, not the full texts. The cloud variability studies are about CPUs and VMs; no peer-reviewed measurement of a free shared T4 or of a gaming-laptop GPU was found. The "2-5% between consecutive runs is normal" figure comes from one ordinary web page. Several GPU-benchmarking blogs that surfaced looked like low-quality content and were not used. Nothing found compares a laptop with a cloud notebook head to head.
