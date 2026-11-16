---
topic: laptop-overnight-heavy-jobs
area: Agent setup
question: Is running heavy agent jobs (GPU, all-core CPU) on a personal laptop every night unattended a common choice, and what are the risks beyond heat wear?
checked: 2026-11-16
review_months: 12
status: current
---
# Heavy agent jobs on a personal laptop every night

- **Question:** Do people commonly let agents run heavy GPU or CPU jobs on their own laptop overnight, every night, while they sleep? What are the risks, beyond the heat wear covered in `findings/laptop-thermal-tiers`?
- **Checked:** 2026-11-16
- **Evidence strength:**
  - *Common practice, anecdotal:* overnight training on a laptop (buying guides, forums, a repair shop).
  - *Official guidance:* unattended charging (fire services, insurers). None of it is specific to a laptop under load.
  - *Common practice, mostly vendor sources:* agent security when unattended.
  - *No data found:* how often people do this, or incident rates.

## Finding

- **Common, but as an occasional job, not a nightly duty cycle.** Laptop and ML buying guides list "train models overnight" as a normal use for fine-tuning, LoRA/QLoRA and moderate CV/NLP jobs, and as unrealistic for pretraining. A PyTorch forum answer and a repair shop treat overnight runs as normal. Both add conditions: a hard surface, clean vents, and a power limit or a quieter mode, which trades speed for heat. One hobbyist built a duty-cycle throttler for a laptop RTX 4060 because undervolting alone didn't keep it cool. No source counts how many people run heavy jobs *every* night, and no source says it is safe for years. Wear evidence is in `findings/laptop-thermal-tiers`: fans, paste and dust wear first, and no GPU lifetime data was found.
- **Throttling protects the chip but signals a problem.** ASUS ROG's guide calls throttling a built-in safety feature. It also says constant throttling means the cooling needs fixing. Dust and dried paste make overnight heat worse. A repair shop suggests cleaning vents every 6 months and repasting every 2 years; that's a seller's rough interval.
- **Fire safety: official bodies advise against unattended overnight charging.**
  - Victoria's CFA says fire risk is higher when you are asleep or away while devices charge, and advises against charging overnight.
  - London Fire Brigade warns against covering chargers and against using a laptop lead in bed.
  - NFU Mutual (an insurer) says unplug once charged, and don't charge while asleep or away.
  - The Hartford (an insurer) ties lithium-ion fires to overnight charging on flammable surfaces.

  None of these addresses a laptop that is plugged in *and* under load. A laptop running overnight jobs is necessarily plugged in all night. What the sources agree on:
  - a hard, non-flammable surface with clear vents (never a bed, sofa or carpet);
  - the original or a certified charger;
  - nothing covering the charger.

  A charge cap ("conservation mode") lowers battery wear (`findings/laptop-thermal-tiers`). No source says whether it changes the fire risk.
- **Agent safety: the unattended part is the larger risk.**
  - Guides agree that an agent can do damage without any attacker, for example deleting files through a reasoning error.
  - Prompt injection can come from a README, web page, dependency or code comment. The Cline VS Code extension compromise is the documented case: it leaked npm release tokens.
  - On a personal machine the agent runs with the user's permissions, so the user's credentials and SSH keys are within reach.
  - Common mitigations:
    - a container or VM with no host mounts;
    - restricted network access;
    - short-lived, least-privilege tokens;
    - destructive and network commands kept off auto-approve lists.

  The sources also report sandbox bypasses. One guide says a fully locked-down agent cannot run unattended for long, so there's a trade-off. Most of these sources are security vendors.
- **The free cloud alternative moves both the heat and the blast radius off the laptop.** Free GPU quota (Kaggle, Colab) is the usual alternative for long GPU jobs. The laptop stays cool and the job can't touch local files. Quota and session limits apply.
- **What can be logged (checker's synthesis from `findings/laptop-thermal-tiers` and the sources above; no source gives wear per night).** Per night: hours under heavy load, heat-cool cycles (a swing of 25 C or more; solder fatigue follows the cycle profile, Coffin-Manson), and GB written to the SSD (write endurance). Slow readings, for trends: battery full-charge capacity and cycle count, disk SMART or Windows reliability counters (wear, temperature, power-on hours, errors; administrator rights or `smartctl` needed on the laptop checked), Windows hardware-error (WHEA) and unexpected-shutdown events, and a fixed 20-minute cooling reference at the same power mode: more heat at the same clock means dust or dried paste. This turns "damage per night" into a trend, which is all the evidence supports. Implemented in `scripts/laptop_health.py`.
- **Checker's synthesis (not a published standard):** heavy nightly jobs on a laptop are a common hobbyist and student choice, not an engineering norm. It is reasonable when all of these hold:
  1. The surface is hard, the vents are clean, the charger is original, and the room has a working smoke alarm.
  2. Power is capped or a quiet mode is on, and a temperature log is checked each morning against a trigger set in advance.
  3. GPU and RAM jobs are serialised by a lock (`findings/agent-process-and-resource-control`).
  4. The agent's permissions leave out destructive commands, credential files and outward-facing actions (merge, deploy, spend).
  5. Long GPU jobs go to free cloud quota when the laptop doesn't need to time them (`findings/benchmark-local-vs-shared-gpu`).
  6. The morning review capacity sets how much is started (`findings/overnight-agent-runs`).

## Sources

- [DEV: a duty-cycle throttler for a laptop RTX 4060](https://dev.to/yaro_dev/i-built-a-duty-cycle-throttler-for-my-rtx-4060-because-undervolting-wasnt-enough-2onn) (community post, anecdotal).
- [PyTorch forum: laptop shuts down while training](https://discuss.pytorch.org/t/laptop-shuts-down-while-trainining/72711/2) (forum answer).
- [Repair shop: 3 a.m. thermal runaway laptop stories](https://www.laptoprepairworld.com/blog/3am-thermal-runaway-laptop-stories/) (commercial, anecdotal).
- [AI Agents Kit: local LLMs on a gaming laptop](https://aiagentskit.com/blog/local-llms-gaming-laptop/) (blog; "train models overnight" feasibility).
- [ASUS ROG: what is thermal throttling](https://rog.asus.com/in/articles/guides/what-is-thermal-throttling/) (vendor guide).
- [CFA Victoria: charging and battery safety](https://www.cfa.vic.gov.au/plan-prepare/fires-in-the-home/charging-and-battery-safety) (fire service, official).
- [London Fire Brigade: batteries and chargers](https://london-fire.gov.uk/safety/the-home/electrical-items/batteries-and-chargers) (fire service, official).
- [NFU Mutual: limit the risk of a lithium battery fire](https://www.nfumutual.co.uk/news-and-stories/how-to-limit-the-risk-of-a-lithium-battery-fire-in-your-home/) (insurer).
- [The Hartford: lithium-ion batteries](https://www.thehartford.com/insights-center/home/lithium-ion-batteries) (insurer).
- [NTU Singapore: is it safe to charge overnight](https://www.ntu.edu.sg/erian/news-events/news/detail/is-it-safe-to-charge-my-phone-overnight-your-battery-charging-questions-answered) (university Q&A; no quantitative frequency).
- [Notebookcheck: HP laptop explodes during overnight charging](https://www.notebookcheck.net/HP-laptop-explodes-during-overnight-charging-and-burns-down-a-Letchworth-store.293278.0.html) (tech press, single incident).
- [Software Mansion: agentic engineering security](https://agentic-engineering.swmansion.com/becoming-productive/security/) (practitioner guide).
- [Graham Brooks: sandboxing AI coding agents](https://www.grahambrooks.com/post/ai-coding-isolation/) (blog).
- [Docker: coding agent horror stories](https://www.docker.com/blog/coding-agent-horror-stories-the-command-you-already-approved/) (vendor blog).
- [Straiker: threat research, coding agents](https://www.straiker.ai/report/threat-research-vol-i/03-coding-agents) (security vendor report).
- [Xebia: risks of unprotected agents](https://xebia.com/blog/the-risks-of-unprotected-agents-and-how-to-mitigate-them/) (consultancy blog).

## Limits

- No survey or count says how many people run heavy jobs on a laptop every night, so "common" rests on guides and forum posts.
- Fire guidance covers charging in general, not a laptop plugged in under sustained load. No incident rate was found for laptops running overnight jobs; the one press report is a single laptop that was charging, with its load unknown.
- The agent-security figures (such as one vendor's share of attacks reaching code execution) come from vendor testing.
- No source compared the risk of an agent left unattended overnight with one left unattended during the day.
- Thermal and battery wear are in `findings/laptop-thermal-tiers`. Keep-awake mechanics are in `findings/keep-awake-long-jobs`.
