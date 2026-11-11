# LoRA vs QLoRA

- **Question:** For fine-tuning a small language model (about 0.5B to 7B), should a project use 16-bit LoRA or QLoRA (LoRA on a 4-bit quantized base), and which is more in demand in research and hiring?

- **Finding:**
  - **Quality:** the QLoRA paper reports that 4-bit NF4 with double quantization matches 16-bit LoRA and 16-bit full fine-tuning (MMLU 53.1 vs 53.0 for LLaMA 7B to 65B; GLUE up to 3B). Unsloth's own guide says 16-bit LoRA is slightly faster and slightly more accurate, and that its dynamic 4-bit quants have recovered most of QLoRA's accuracy loss. A small medical-domain study found LoRA slightly ahead of QLoRA and faster to train (40 vs 55 minutes). So the gap is about a point or less, task-dependent, and QLoRA is slower per step because of dequantization.
  - **Memory:** QLoRA exists to save memory. Unsloth puts 16-bit LoRA at about 4 times QLoRA's VRAM for a large model; at about 1B parameters the difference is small (a third-party estimate: 6 GB vs 4 GB). Checker's inference: below about 1B on a GPU with 8 GB or more, there is little reason to quantize.
  - **Rule of thumb in the sources:** use QLoRA when memory is the limit; use 16-bit LoRA when the model fits, because it is slightly better and faster. Train and serve in the same precision. Merge adapters into a 16-bit base, not an NF4 one.
  - **What matters more than the choice:** "LoRA Without Regret" (Thinking Machines, 2025) finds LoRA matches full fine-tuning when adapters go on all weight matrices (MLP included, not attention only), the learning rate is about 10 times the full fine-tuning rate, and the dataset fits the adapter's capacity. Biderman et al. (2024) is the more cautious earlier result: LoRA learns less than full fine-tuning on code and math, and forgets less.
  - **Demand:** 2026 LLM-engineer postings name "LoRA, QLoRA" together as one parameter-efficient fine-tuning (PEFT) skill, usually next to adapters, DeepSpeed/FSDP, DPO/RLHF and evaluation. No source separates the two terms by how often postings ask for each. Checker's inference: naming both on a resume (as "LoRA/QLoRA") costs nothing and matches the postings; the choice of which one a project actually used should follow what was run.
  - Fine-tuning is a specialty: one recruiter says it appears in about half of LLM job descriptions drafted and in a much smaller share of actual roles; one market breakdown gives about 18% of postings. RAG and evaluation are the more common requirements.

- **Sources:**
  - [QLoRA: Efficient Finetuning of Quantized LLMs (NeurIPS 2023)](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1feb87871436031bdc0f2beaa62a049b-Abstract.html), peer-reviewed paper.
  - [Unsloth, fine-tuning guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide) and [LoRA hyperparameters guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide), tool vendor docs.
  - [LoRA Without Regret](https://thinkingmachines.ai/blog/lora/), research lab blog post (not peer reviewed); also in [TRL documentation](https://huggingface.co/docs/trl/main/en/lora_without_regret).
  - [LoRA Learns Less and Forgets Less](https://arxiv.org/html/2405.09673v2), arXiv paper.
  - [LoRA vs QLoRA: choose by VRAM, then check quality](https://gpuperhour.com/blog/lora-vs-qlora-fine-tuning) and [MDD-LLM (medical-domain LoRA vs QLoRA timing)](https://arxiv.org/pdf/2505.00032), secondary.
  - Job postings and market breakdowns: [Jobgether LLM Engineer](https://jobgether.com/offer/6a5a74d4ac00a71a5a98fb39-llm-engineer), [aijobs.net fine-tuning posting](https://aijobs.net/job/3I3kTwO4QJyqAKM/apply/), [LLM engineering market analysis](https://mshojaei77.github.io/market_analysis.html), [kore1 job-description template](https://www.kore1.com/llm-engineer-job-description-template/).

- **Limits:**
  - The quality gap is measured on MMLU, GLUE and one small medical study, not on small-model generative QA. Validate on the task.
  - Most size and memory numbers are from guides and blogs, not controlled measurements.
  - Demand evidence is a handful of postings, recruiter blogs and aggregator pages, with unverified percentages and salary claims. It does not show which of the two terms is asked for more often.
  - "LoRA Without Regret" does not compare quantized and 16-bit bases.

- **Checked:** 2026-11-12
