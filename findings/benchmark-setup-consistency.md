# Benchmark setup consistency

- **Question:** Must every benchmark run on the same hardware and configuration, or may results come from different setups (a laptop GPU, then a cloud GPU)?
- **Checked:** 2026-11-11

## Finding

- **Results compared with each other share one setup.** MLPerf requires a set of results reported together to come from the same system and framework, and each submission publishes a system description (hardware, software, framework). The baseline and the change being measured run on that same setup.
- **Different setups are allowed; each result names its own.** No source asks that all benchmarks over time use one machine. The rules ask for disclosure instead: hardware (processor, memory, accelerator) and software versions (Benchmarking Crimes; MLPerf system descriptions; the inference-benchmark reporting list in [llm-inference-memory-calibration](llm-inference-memory-calibration.md)).
- **Speedups do not transfer across hardware.** The same change can give different gains on different GPUs or GPU counts. One vendor report shows a parallelism change at about -0.6% on one H100 and +13% on two H100s. A result from one setup is not a correction of another; it is a second data point.
- **Report the baseline and absolute numbers, not only ratios.** Hoefler and Belli (SC15) say to state the base case and its absolute performance, and never to report ratios without absolute values. Benchmarking Crimes lists a missing or non-standard baseline and relative-only figures as flaws.
- **Checker's inference** (not stated by the sources): when a rerun changes both the setup and the workload (new GPU and new samples), also rerun the old workload on the new setup. Otherwise the two effects cannot be told apart. This is the one-factor-at-a-time reasoning of experimental design, applied here without a source that states it for benchmarks.

## Sources

- [MLPerf inference rules](https://github.com/mlcommons/inference_policies/blob/master/inference_rules.adoc) and [submission rules](https://github.com/mlcommons/policies/blob/master/submission_rules.adoc) (industry consortium, official).
- [Heiser, Systems Benchmarking Crimes](https://gernot-heiser.org/benchmarking-crimes.html) and [van der Kouwe et al., Benchmarking Crimes, arXiv 1801.02381](https://arxiv.org/pdf/1801.02381) (academic).
- [Hoefler and Belli, Scientific Benchmarking of Parallel Computing Systems, SC15](https://evaluate.inf.usi.ch/node/366) (peer-reviewed).
- [Apolo, multi-GPU LLM inference benchmarks](https://docs.apolo.us/index/apolo-console/apps/available-apps/llm-inference/multi-gpu-benchmarks-report) (vendor report).

## Limits

The MLPerf and Hoefler points come through search summaries; the exact rule texts were not read. The cross-GPU example is one vendor report, not a study. No source found gives a method for comparing one speedup measured on two machines.
