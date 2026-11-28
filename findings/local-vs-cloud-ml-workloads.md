---
topic: local-vs-cloud-ml-workloads
area: ML systems
question: Is it a good idea to run heavy ML/AI work (training, fine-tuning, inference) on a personal machine rather than a cloud or hosted service, and do production apps use hosted third-party models?
checked: 2026-11-28
review_months: 6
status: current
---
# Heavy ML/AI work on a personal machine or in the cloud

- **Question:** Is it a good idea to run heavy ML/AI work on a personal local machine? Separate from `laptop-overnight-heavy-jobs` and `laptop-thermal-tiers`, which assume the job is local and ask about its risks; this entry covers where it should run (cost, access, safety of model files).
- **Checked:** 2026-11-27 (hosted models in production: 2026-11-28)
- **Evidence strength:**
  - *Official docs:* Colab free-tier limits, pickle and `torch.load` risk, Dell battery swelling.
  - *Sample or survey:* academic researchers' compute (50 respondents).
  - *Vendor or single source:* cost break-even figures.
  - *No data found:* an independent comparison for one person with a consumer GPU; any body that recommends for or against local ML work.

## Finding

No source gives a general yes or no. It depends on how many hours the hardware is busy, whether the job fits it, and what the cloud option limits.

**Cost**

- One person, consumer GPU (one tool vendor's worked example): break-even hours = purchase price / (cloud price per hour - electricity per hour). With example inputs of a $2,000 RTX 4090, 450 W at $0.14/kWh and rentals of $0.34 or $0.89/h, it is about 7,200 or 2,400 GPU hours (about 300 or 100 days running 24/7). The host PC, resale value and the user's time are left out, and the author calls price, wattage and tariff example inputs, not market data.
- Servers (a cloud GPU seller, so biased toward cloud): cloud wins under about 70% sustained utilisation over 3 years, for an 8x H100 server with staff and colocation. The same page contradicts itself on whether owning wins at high utilisation. Not applicable to a personal machine.
- Cloud also wins for hardware most buyers cannot get (H100, B200) and for bursts (same single-user source).

**Free cloud has limits too**

- Colab free: at most 12 hours, "depending on availability and your usage patterns"; idle runtimes time out; resources are not guaranteed and the usage limits are not published.
- Kaggle: about 30 GPU hours a week and 9 or 12 hour sessions are third-party figures that disagree; no official page was read. Read the quota shown in the account.

**Who uses what**

- Survey of 50 academic researchers (April 2024): 85% reported no cloud budget; they typically use on-premises compute from their institution, 1-8 GPUs for days or weeks. This says nothing about privately owned machines.

**Safety, local or not**

- Loading a pickle model file can run arbitrary code (Hugging Face docs). `torch.load` defaults to `weights_only=True` in the 2.15 docs, which still say never to load data from an untrusted source. Prefer safetensors; Hub pickle scanning is "not 100% foolproof".
- (inference: findings/local-vs-cloud-ml-workloads) On a personal machine such code runs next to the owner's files and credentials; in a throwaway hosted notebook it reaches less. See the agent-security lines in `laptop-overnight-heavy-jobs`.

**Hardware wear**

- Lithium-ion batteries can swell with age, charge cycles or high heat (Dell). GPU, fan and battery wear, fire safety and overnight runs: `laptop-thermal-tiers`, `laptop-overnight-heavy-jobs`. No laptop GPU lifetime data was found there.

**Checker's synthesis** (inference: findings/local-vs-cloud-ml-workloads), not a published standard:

- **Local is a good idea** when the job fits the GPU memory already owned; it is short or interactive (debugging, small fine-tunes, quantised inference); it needs data that should not leave the machine, a local service, or timing of that machine; and model files come from trusted sources.
- **Prefer free or rented cloud** when the job runs for hours with full GPU or CPU load on a laptop, needs more memory than the machine has, is a one-off burst, or loads untrusted model files (isolation still needed).
- **Buy hardware** only after estimating real GPU hours against the break-even formula with local prices; occasional use does not repay it.
- A desktop is likely the better local choice than a laptop for sustained load (cooling, no battery). No source was checked for this; treat it as open.

## Hosted third-party models in production (added 2026-11-28)

- **Evidence strength:** *sample or survey* for market share; *vendor or single source* for the default. No source found gives the share of production LLM applications that call a vendor's API against self-hosting.
- Open-source models held 11% of estimated enterprise LLM API usage, down from 19% (Menlo Ventures, 495 US decision-makers, November 2025). This is open against closed models, not hosted against self-hosted, and leaves self-hosted inference out.
- Several 2026 consultancy and vendor guides call a managed API the default and keep self-hosting for data residency or high steady volume; their break-even volumes disagree widely (search summaries).
- (inference: findings/local-vs-cloud-ml-workloads) For a low-traffic application with no GPU host, a hosted vendor model in production is the usual choice; it is not a documented standard.
- Sources: [Menlo Ventures, State of Generative AI in the Enterprise 2025](https://menlovc.com/perspective/2025-the-state-of-generative-ai-in-the-enterprise/) (VC survey; the firm invests in model vendors); [Self-hosted vs API guide](https://neevcloud.com/blogs/open-weight-vs-closed-models-self-host-or-call-an-api) (vendor blog, search summary). Prices: `hosted-llm-api-prices`.

## Sources

- [Hugging Face: pickle scanning](https://huggingface.co/docs/hub/security-pickle) (official docs).
- [PyTorch 2.15: torch.load](https://docs.pytorch.org/docs/2.15/generated/torch.load.html) (official docs).
- [Google Colab FAQ](https://research.google.com/colaboratory/faq.html) (official docs).
- [Dell: handling swollen lithium-ion batteries](https://www.dell.com/support/manuals/dell/swollenbattery) (official docs).
- [$100K or 100 Days, arXiv 2410.23261](https://arxiv.org/abs/2410.23261) (peer-reviewed survey, COLM 2025).
- [PromptQuorum: local LLM vs cloud GPU cost](https://www.promptquorum.com/local-llms/local-llm-vs-cloud-gpu-cost) (single source, tool vendor; updated 2026-11-22).
- [Spheron: on-premise vs cloud inference](https://www.spheron.network/blog/llm-inference-on-premise-vs-cloud/) (vendor blog; sells cloud GPUs).

## Limits

- Cost figures are example calculations, mostly in US prices and tariffs; second-hand and mid-range cards were not priced.
- Privacy and legal reasons for local processing were not searched.
- The survey is small, academic and from 2024, about pre-training.
- No NIST or OWASP document on model-file loading turned up.
- Pages were read through a fetch agent; part of the arXiv page was only summarised.
