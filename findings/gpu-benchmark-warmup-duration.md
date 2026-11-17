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
- **Checker's synthesis:** a fixed 10 minutes per setting measures a plateau that is reached in a few minutes. A better rule: warm up until the temperature changes by less than 1 °C over 2 minutes (at most 8 minutes), then measure for 3 minutes, with a 3-minute rest between settings. For four settings that is about 25 minutes instead of about 55. The first run after a change (new driver, cleaned fans, new paste) is the one worth a full 20 minutes, to confirm the plateau.

## Sources

- [NVIDIA CUTLASS: GEMM performance measurement methodology guidelines](https://docs.nvidia.com/cutlass/4.6.0/media/docs/cpp/gemm_performance_measurement_methodology_guidelines.html) (official docs; warm up until clocks and power settle).
- [Guru3D: graphics card temperatures (warm-up of at least 15 minutes)](https://www.guru3d.com/review/undervolting-the-yeston-radeon-rx-7800-xt/page-6/) (hardware review site).
- [XMG support: is my system's performance and temperature within expectations](https://help.xmg.gg/hc/en-gb/articles/17824812141213-How-can-I-tell-if-my-system-s-performance-and-temperatures-are-within-expectations) (laptop maker support page).
- [TechnoLynx: how to benchmark a PC for AI, the steady-state test protocol](https://technolynx-site.pages.dev/post/benchmark-pc-ai-steady-state-protocol) (vendor blog; 5-minute warm-up, 20 minutes minimum).
- [MLPerf Power (arXiv 2410.12032)](https://arxiv.org/abs/2410.12032) (peer-reviewed; 60 s minimum window).
- [MLPerf Mobile inference benchmark (arXiv 2012.02328)](https://arxiv.org/pdf/2012.02328) (peer-reviewed; 60 s, room temperature, cooldown breaks).

## Limits

The warm-up lengths come from one review site, one laptop maker and one blog; none is a laptop standard. SPEC's power benchmark rules were not found. The plateau time is one measurement on one laptop, at a capped clock.
