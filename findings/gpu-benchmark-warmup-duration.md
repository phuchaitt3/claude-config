---
topic: gpu-benchmark-warmup-duration
area: Software process
question: How long must a laptop GPU benchmark (speed, temperature, power at a given clock setting) run before the reading is trustworthy, and is a fixed 10-20 minutes per setting standard?
checked: 2026-11-17
review_months: 12
status: current
---
# How long a laptop GPU benchmark must run

- **Question:** How long must a laptop GPU benchmark (speed, temperature, power at one clock setting) run before the reading is trustworthy, and is a fixed 10-20 minutes per setting standard?
- **Checked:** 2026-11-17
- **Evidence strength:** *vendor or single source* for the warm-up lengths (a GPU review site, a laptop maker's support page, an AI-benchmarking blog); *official docs* for NVIDIA's GEMM methodology (no fixed time) and *peer-reviewed* for the MLPerf rules (60 s minimum, which is a run length, not a thermal warm-up); *sample* (one machine, one run) for the measured plateau below.

## Finding

- **No fixed standard time; the common rule is to warm up until the readings plateau.** NVIDIA's CUTLASS measurement guidelines give no number: warm up until clocks stabilize, and for fixed-power tests until power draw settles. A laptop maker's support page says a GPU reaches thermal saturation within a few minutes of full load. A GPU review site warms the card at least 15 minutes before every test because a cold card can briefly beat a warmed one. An AI-benchmarking blog suggests a 5-minute warm-up and calls 20 minutes from cold the minimum for a steady-state run, treating minutes 5-10 as transient. These disagree because cooling designs differ; the sources are not laptop-specific standards.
- **MLPerf sets run length and conditions, not a warm-up.** MLPerf Power measures at least 60 s (a shorter workload loops until then) and averages power over valid samples. MLPerf Mobile requires at least 60 s and 1,024 samples in single-stream mode, a 20-25 °C room, a break of 0-5 minutes between tests and 10 minutes between repeated suite runs.
- **Measured on the checked laptop (GTX 1660 Ti, clock capped at 1350 MHz, Ollama qwen2.5:3b back-to-back, 2026-11-17):** GPU temperature was 59 °C at minute 1 and stayed within 60.2-61.8 °C (five-minute means) over 20 minutes; speed was 72.6 tok/s in the first five requests and 71.5 in the last five (1.5% apart). The plateau came within 1-2 minutes at that clock. An uncapped run starts hotter and may take longer; not measured.
- **Stopping when stable is the established method in software benchmarking, with known weaknesses.** Georges et al. (OOPSLA 2007) call the run steady once the coefficient of variation of the last k iterations falls below a threshold (a follow-up used 2% over 10 iterations); Laaber et al. compare variants using confidence-interval width and divergence measures; newer work uses change-point detection. Barrett et al. (2017) found the heuristic can declare steady state where none exists, and that many benchmarks never settle, so a maximum time and a "not stable" label are needed. These are for software warm-up (JIT, caches), not heat; the checker transfers the idea to temperature and speed.
- **Checker's synthesis:** a fixed 10 minutes per setting measures a plateau that is reached in a few minutes. Start with a minimum (90 s) and extend only until stable: stable when the GPU temperature varies by at most 1 °C over the last 60 s and tokens/s varies by at most 2% (coefficient of variation) over the last 5 requests; stop at a maximum of 8 minutes and record "not stable". Measure over that stable window, with no separate measuring phase. Run the settings from the lowest clock to the highest, so the laptop only ever heats up between settings and needs no rest. On the checked laptop this is expected to take about 2 minutes a setting (about 10 minutes for four), against about 55 for a fixed 10 minutes each. The first run after a change (new driver, cleaned fans, new paste) is worth a full 20 minutes, to confirm the plateau.

## Sources

- [NVIDIA CUTLASS: GEMM performance measurement methodology guidelines](https://docs.nvidia.com/cutlass/4.6.0/media/docs/cpp/gemm_performance_measurement_methodology_guidelines.html) (official docs; warm up until clocks and power settle).
- [Guru3D: graphics card temperatures (warm-up of at least 15 minutes)](https://www.guru3d.com/review/undervolting-the-yeston-radeon-rx-7800-xt/page-6/) (hardware review site).
- [XMG support: is my system's performance and temperature within expectations](https://help.xmg.gg/hc/en-gb/articles/17824812141213-How-can-I-tell-if-my-system-s-performance-and-temperatures-are-within-expectations) (laptop maker support page).
- [TechnoLynx: how to benchmark a PC for AI, the steady-state test protocol](https://technolynx-site.pages.dev/post/benchmark-pc-ai-steady-state-protocol) (vendor blog; 5-minute warm-up, 20 minutes minimum).
- [MLPerf Power (arXiv 2410.12032)](https://arxiv.org/abs/2410.12032) (peer-reviewed; 60 s minimum window).
- [MLPerf Mobile inference benchmark (arXiv 2012.02328)](https://arxiv.org/pdf/2012.02328) (peer-reviewed; 60 s, room temperature, cooldown breaks).

- [Acolyer's summary of Georges et al., statistically rigorous Java performance evaluation](https://blog.acolyer.org/2017/11/06/statistically-rigorous-java-performance-evaluation/) (secondary summary of a peer-reviewed paper; the paper itself was not read).
- [Barrett et al.: virtual machine warmup blows hot and cold (arXiv 1602.00602)](https://arxiv.org/pdf/1602.00602v4) (peer-reviewed; critique of the steady-state heuristic).
- [Laaber et al.: AI-driven Java performance testing, balancing result quality with testing time (arXiv 2408.05100)](https://arxiv.org/pdf/2408.05100) (academic; stopping criteria).

## Limits

The stable-window thresholds (1 °C over 60 s, 2% over 5 requests, 90 s minimum, 8 minutes maximum) are the checker's choice, not from a source; they were set from one run and should be reviewed after the first benchmark. The Georges method was read through a secondary summary.

The warm-up lengths come from one review site, one laptop maker and one blog; none is a laptop standard. SPEC's power benchmark rules were not found. The plateau time is one measurement on one laptop, at a capped clock.
