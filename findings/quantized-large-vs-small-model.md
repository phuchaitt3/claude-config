# Quantized larger model or smaller full-precision model

- **Question:** At a fixed memory budget, is a larger model quantized to 4 bits generally better than a smaller model kept in 16-bit, and is "4-bit is nearly free" true for models under 1B parameters?

- **Finding:**
  - **Same weight memory, bigger and quantized usually wins.** Dettmers and Zettlemoyer (35,000+ experiments, 19M to 176B parameters) find 4-bit "almost universally optimal" for zero-shot accuracy per total model bit: a 30B model at 8 bits and a 60B model at 4 bits cost the same bits, yet accuracy differs substantially (in favour of the larger one at 4 bits). Badshah and Sajjad (7B to 70B instruct models) report that larger models hold accuracy at 4-bit on most tasks and beat smaller high-precision models at similar memory.
  - **Small models are the exception.** A 1B to 405B study of instruction-tuned models (four quantization methods, 13 datasets) reports that "smaller models can suffer severe accuracy drops at 4-bit", while 70B-scale models stay stable (FP8 is the safest at every size). A preprint on small models reports Qwen-0.6B is less robust at extreme low bit-widths, with a few layers much more critical than others. A NeurIPS 2026 submission finds 4-bit raises missed tool calls in small models but not mid-size ones, and says to validate each checkpoint instead of assuming from a size threshold. So "4-bit is nearly free" is a result for roughly 7B and up, not for 0.5B.
  - **The effect is task- and model-dependent.** Large drops are concentrated in specific model-and-task pairs (multilingual math, tool calling); a broader study finds typical degradation of 1 to 4%. Sensitivity differs by family (one study: Llama and Mistral fragile in early layers, Qwen and Gemma more uniform).
  - **"Little redundancy" is the checker's wording, not a source's.** The sources show small models lose more and have a few critical layers; "less redundancy" is an interpretation of that, and "16 levels per weight" is just how NF4 is defined (4 bits).
  - **Checker's inference on when "bigger and quantized" pays:** only when memory is the binding limit and the quantized model's runtime cost is acceptable. Weight memory is only part of inference memory (the KV cache and activations grow with batch size and prompt length), and bitsandbytes dequantization can make a quantized model no faster than fp16 (int8 slower). If the small model already fits with room to spare, quantizing a larger one trades speed and accuracy risk for no needed saving.

- **Sources:**
  - [The case for 4-bit precision: k-bit inference scaling laws (Dettmers and Zettlemoyer)](https://arxiv.org/abs/2212.09720), arXiv paper (ICML 2023).
  - [Quantifying the Capabilities of LLMs across Scale and Precision (Badshah and Sajjad)](https://arxiv.org/abs/2405.03146), arXiv preprint; checked from its abstract and summaries only.
  - [Evaluation of quantized instruction-tuned LLMs, 1B to 405B](https://arxiv.org/abs/2409.11055), arXiv paper; abstract read, no figures for the small-model drop.
  - [Layer-wise information effectiveness for post-training quantization in small language models](https://arxiv.org/html/2508.03332v1), arXiv preprint.
  - [Compression breaks discipline: quantization and missed tool calls](https://neurips.cc/virtual/2026/171153), conference submission page.
  - [Two failure modes of LLM quantization](https://arxiv.org/pdf/2604.19884), arXiv preprint (family sensitivity), read through a search summary only.

- **Limits:**
  - The scaling-law papers measure accuracy per total bit on benchmarks (zero-shot, instruct); they say little about latency, serving throughput or generative QA in a low-resource language.
  - Several sources are preprints read from abstracts or search summaries; no source gives a clean size threshold below which 4-bit fails.
  - No source here compares a larger quantized model to a smaller fp16 model for the same task at sub-2B scale with measured speed. That comparison needs a run on the actual task.

- **Checked:** 2026-11-12
