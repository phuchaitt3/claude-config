# Low disk space alerts: thresholds

- **Question:** At what free-space level should a machine warn about a filling drive, and is there a standard threshold?
- **Finding:**
  - **No authoritative standard.** One monitoring vendor's knowledge base notes there is no Microsoft best-practice figure for how much free space to leave, so the number is the operator's choice.
  - **Common shape: two tiers by percent, plus an absolute floor.** Monitoring vendors' guides converge on a warning at about 20% free and a critical alert at about 10% free. One example uses only a 10% free threshold. Percent scales with drive size. On a large drive a percent can stay quiet while hundreds of GB remain, and on a small one it can fire too late, so operators add a fixed GB floor. One operator alerts below 10 GB free on `C:` because Windows Updates fail below that.
  - **Free vs available:** on Linux, alert on the space available to unprivileged users, not total free, because reserved blocks cannot be used by ordinary processes.
  - *Checker's inference for a laptop shared by agents:* warn per drive holding a working directory, when free space is below 10% or 10 GB on the system drive, whichever comes first. Warn only, rate-limited; deleting files stays a human or explicit-task action (see `docker-disk` for what is safe to prune).
- **Evidence strength:** *common practice*. Several monitoring vendors and operators agree on the shape; the numbers are conventions, not measured.
- **Sources:**
  - [Level, disk usage monitor](https://docs.level.io/en/articles/13908774-disk-usage-monitor) (vendor docs; 20% / 10% tiers)
  - [Datadog, monitoring available disk space](https://docs.datadoghq.com/monitors/guide/monitoring-available-disk-space/) (vendor docs; available vs free, 10% example)
  - [LogicMonitor community, disk space alerting](https://community.logicmonitor.com/forum/product-discussions-68/topic/how-do-you-handle-disk-space-alerting-1733/) (operator forum; 10 GB floor on C:)
  - [Quest KB, 80% disk-full threshold](https://support.quest.com/kb/4247105/why-the-disk-full-threshold-is-it-set-to-80-in-the-disk-percentage-used-alarm-) (vendor KB; no Microsoft guideline)
  - [SolarWinds THWACK, volume threshold practices](https://thwack.solarwinds.com/discussion/comment/109993) (operator forum)
- **Limits:** One standard search, read through search summaries. Sources are about servers and fleets, not developer laptops or CI build agents. No source measures what happens below a given threshold apart from the Windows Update anecdote.
- **Checked:** 2026-11-14
