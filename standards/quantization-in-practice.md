# Where quantization is used in practice, and how much jobs ask for it

- **Question:** In real research and applications, when is quantization the natural choice (as opposed to using a smaller model), and how often do LLM job postings ask for it?

- **Finding:**
  - **On-device and local use is the natural home.** Memory limits decide the model, so a larger model is squeezed in with 4-bit weights. The runtime is usually llama.cpp (GGUF format, also Ollama and LM Studio) on a CPU, a consumer GPU or Apple Silicon. A mobile-device benchmark finds 4-bit gives peak or near-peak speed in both prompt processing and decoding with accuracy close to 16-bit; the loss appears mainly at 3 bits and below.
  - **Why it speeds up there.** Token-by-token decoding at small batch is limited by memory bandwidth, not arithmetic (arithmetic intensity about 1 in fp16; weight reads dominate traffic). Weight-only 4-bit cuts the bytes read, which is enough for a speedup (AWQ paper; DecDEC paper). Prompt processing is compute-bound and gains less. A speedup also needs a cheap dequantization kernel.
  - **GPU serving is the second home.** Teams quantize to fit more concurrent requests and cut cost: weights shrink, which frees KV-cache memory. Common choices on NVIDIA GPUs with vLLM: FP8 where the hardware supports it (near-lossless in the vendor numbers), AWQ with Marlin kernels as the usual 4-bit default, GPTQ for broad compatibility. GGUF is for local use and is marked experimental in vLLM. Cost-saving figures (60 to 80%) are vendor claims from their own workloads.
  - **Fine-tuning:** QLoRA (4-bit base) is used when the model does not fit in 16-bit during training; see `standards/lora-vs-qlora`.
  - **Checker's inference:** bitsandbytes NF4 and int8 (what a research script uses) are loaders for training and experiments, not what production serving or phones use; and a run that is compute-bound, such as large batches on a server GPU, will not show the bandwidth gain, so a measured slowdown there is consistent with these sources rather than contradicting them.
  - **Jobs:** quantization is an explicit requirement in inference-optimization postings (for example a posting asking for QAT, PTQ, FP8, INT8, INT4, AWQ, GPTQ or SmoothQuant experience; a "Quantized Inference" engineer title), where vLLM, SGLang or TensorRT-LLM experience is near universal. In general LLM engineer and ML engineer postings it is sometimes a plus and often absent. No source measures how often it appears across all LLM roles.

- **Sources:**
  - [Quantization in practice: GPTQ vs AWQ vs GGUF](https://theaiengineer.substack.com/p/quantization-in-practice-gptq-vs), [LLM quantization guide, 2026 (Prem AI)](https://blog.premai.io/llm-quantization-guide-gguf-vs-awq-vs-gptq-vs-bitsandbytes-compared-2026), [vLLM serving guide](https://thakicloud.github.io/en/llmops/llm-quantization-vllm-serving-unsloth/), vendor and blog posts.
  - [AWQ: Activation-aware Weight Quantization](https://arxiv.org/pdf/2306.00978), peer-reviewed paper (MLSys 2024); [Understanding LLMs in your pockets: performance study on mobile devices](https://arxiv.org/html/2410.03613v5), arXiv paper; [Pushing the envelope of low-bit LLM via dynamic error compensation](https://arxiv.org/html/2412.20185v1) and [QuIP#](https://arxiv.org/pdf/2402.04396), arXiv papers.
  - Postings: [Second Talent, AI inference engineer](https://www.secondtalent.com/occupations/ai-inference-engineer/), [NVIDIA quantized inference posting](https://hitmarker.net/jobs/nvidia-senior-software-engineer-quantized-inference-4567550), [Together AI inference optimization posting](https://inferencejobs.com/companies/together-ai/jobs/llm-inference-frameworks-and-optimization-engineer), [Inferact inference posting](https://zerogtalent.com/ai-jobs/inferact/member-of-technical-staff-inference-9470565b-c62d-4de9-8b87-26d525ecec49), [GMI Cloud posting](https://jobverse.io/jobs/38062804/machine-learning-engineer-llm--at-gmicloud-remote).

- **Limits:**
  - Format and speed claims come mostly from vendor and blog posts with their own benchmarks that conflict across sources; the academic papers cover specific chips and engines.
  - Job evidence is a handful of postings and aggregator pages; no frequency across LLM roles was found.
  - Nothing here measures quantization for retrieval-augmented QA in a low-resource language.

- **Checked:** 2026-11-12
