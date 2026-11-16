---
topic: monitoring-sample-interval
area: Software process
question: How often do standard tools sample hardware metrics such as GPU temperature, and is a 60-second always-on logger on a laptop light enough to leave running?
checked: 2026-11-17
review_months: 12
status: current
---
# Sampling interval for an always-on hardware logger

- **Question:** How often do standard monitoring tools sample hardware metrics such as GPU temperature, and is a 60-second always-on logger on a laptop light enough to leave running?
- **Checked:** 2026-11-17
- **Evidence strength:** *official standard* for tool defaults (NVIDIA and Prometheus docs); *sample* (one machine, one measurement) for the logger's own cost.

## Finding

- **Defaults sit between 30 and 60 seconds.** NVIDIA's DCGM Exporter collects GPU metrics every 30 s by default (`DCGM_EXPORTER_INTERVAL`, 30000 ms); Prometheus scrapes every 1 minute by default (`scrape_interval: 1m`). Guides call 10-60 s a good range for host metrics, and shorter intervals (DCGM examples use 3-5 s for thermal fields) when short spikes matter.
- **Temperature changes slowly enough for 60 s.** Heat-up under load takes minutes, so a 60 s sample catches trends, sustained heat and minutes above a threshold; it can miss a spike of a few seconds. Thermal throttling time is still caught, because NVIDIA's slowdown counters are cumulative and read at each sample.
- **Measured cost on a 2019 laptop (i7-9750H, GTX 1660 Ti, Windows), 2026-11-17:** the Python logger process used 0.03 s of CPU in 120 s (0.03% of one core) and 8.7 MB of memory. Each sample runs one `nvidia-smi` query: about 0.05 s of CPU and 100 ms wall time (700 ms on a cold first call). At one sample a minute the total is about 0.1% of one core, about 0.01% of the 12-thread CPU. The log grows about 240 bytes a sample: about 0.35 MB a day, 125 MB a year, so it needs rotation within a year if reports read the whole file.
- **Checker's synthesis:** 60 s is at the standard default and its cost is negligible; there is no reason to sample less often. Sampling more often (for example 10 s) would still be light but only helps when spikes of seconds matter, which an overnight heat log does not need.

## Sources

- [NVIDIA DCGM Exporter docs (collection interval, default 30000 ms)](https://docs.nvidia.com/datacenter/dcgm/latest/gpu-telemetry/dcgm-exporter.html) (official docs).
- [Last9: DCGM Exporter setup and metrics guide](https://last9.io/blog/dcgm-exporter) (vendor blog; scrape alignment).
- [Datadog DCGM integration](https://docs.datadoghq.com/integrations/dcgm/) (vendor docs; 3 s example).
- [Prometheus configuration docs (scrape_interval default 1m)](https://prometheus.io/docs/prometheus/2.55/configuration/configuration/) (official docs).
- [OneUptime: what is the right scrape interval for host metrics?](https://oneuptime.com/blog/post/2026-07-31-host-metrics-scrape-interval/view) (vendor blog).
- [Robust Perception: how many scrape intervals should you have?](https://robustperception.io/keep-it-simple-scrape_interval-id) (Prometheus maintainer's blog).

## Limits

No source measures `nvidia-smi` polling overhead; the cost figures are one measurement on one laptop. Telegraf's default (reportedly 10 s) was not confirmed from its docs.
