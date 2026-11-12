# Numeric precision when comparing model sizes

- **Question:** When one model family is compared at several sizes (and quantization formats), is the numeric precision (fp32, fp16, bf16) chosen per model, or held fixed across the comparison; and what happens when a model overflows in fp16?
- **Checked:** 2026-11-12

## Finding

- **Precision is a reported setting, set per run.** The EleutherAI evaluation harness takes `dtype` in each run's model arguments and writes the resolved config to its output file; a 2026 tutorial advises recording backend and dtype with every number. This is how an auditor confirms two runs used the same dtype.
- **Hugging Face `dtype="auto"` means "whatever the checkpoint declares".** It reads `config.json` (falling back to the first floating-point weight). Checkpoints can declare different dtypes, so "auto" can silently give different sizes different precision; an explicit dtype removes that.
- **fp16 can overflow for models trained in bf16, and it is checkpoint-specific.** fp16 tops out near 65,504; bf16 keeps fp32's exponent range (about 3e38) with less mantissa precision (general numerics, not from a search result). "Massive activations" papers report a few scalar activations thousands to 100,000 times larger than typical; a follow-up analysis cites float16 instability for such activations (Gemma-3 as the example). A 2026 benchmarking paper attributes crashes of a Qwen2.5-VL 3B model on a T4 to fp16's narrow range and notes Qwen models are trained in bf16; a Transformers issue on Qwen2-VL reports inf attention weights turning to NaN after softmax. One summary says overflow collapses the whole pass into NaNs. Nothing found says which size of a family will overflow.
- **Precision also moves results that do not crash.** NeurIPS 2025 "Give Me FP32 or Give Me Death?": greedy decoding gives different answers when batch size, GPU count or GPU type change, up to 9% accuracy variation for a 7B distilled model in bf16, with divergence far lower in fp32. A 2026 preprint (abstract only) reports bf16 and fp16 diverging on 49-100% of prompts across six 1.1B-7B models. So dtype is a confound, not a free choice.
- **Checker's inference (no source states it for size sweeps):** compare sizes at one dtype, chosen as the cheapest one in which every compared model produces finite, sensible output; check for NaN or degenerate text before scoring any cell. If one model fails, either move every model to the safer dtype, or exclude that cell and report the failure as a result. Do not mix dtypes silently: speed and memory then compare different things as well as different sizes. For a quantized model, the compute dtype is a separate setting from the weight format and has to be fixed and reported too.

## Sources

- [lm-evaluation-harness architecture and configuration](https://slyracoon23.github.io/blog/posts/2025-03-21_eleutherai-evaluation-methods.html) and [2026 tutorial](https://qaskills.sh/blog/lm-evaluation-harness-tutorial-2026) (community posts about an official tool; the harness's own docs were not opened).
- [Transformers: loading models, `dtype="auto"`](https://huggingface.co/docs/transformers/models) (official docs, read through a search summary).
- [Massive Activations in Large Language Models](https://arxiv.org/abs/2402.17762) and [A Refined Analysis of Massive Activations](https://arxiv.org/pdf/2503.22329) (arXiv papers; the fp16 point comes from a search summary of the second).
- [UVLM: reproducible multimodal benchmarking](https://arxiv.org/pdf/2603.13893) (arXiv preprint; Qwen2.5-VL on T4, fp16 range) and [Demystifying numerical instability in LLM inference](https://arxiv.org/pdf/2606.21023) (arXiv preprint; overflow to NaN).
- [Transformers issue 33312, Qwen2-VL fp16](https://github.com/huggingface/transformers/pull/33312) (community report, via a mirror; its claim that Qwen docs discourage fp16 was not confirmed).
- [Give Me FP32 or Give Me Death? (NeurIPS 2025)](https://arxiv.org/abs/2506.09501) (peer-reviewed) and [Greedy Decoding Is Not Precision-Invariant](https://arxiv.org/pdf/2609.26621) (arXiv preprint, abstract only).

## Limits

Most points were read from search summaries, not full papers. No official Qwen guidance on fp16 versus bf16 was found. No source was found that states "hold dtype fixed across a size sweep"; that rule is inferred from the setup-consistency practice in [benchmark-setup-consistency](benchmark-setup-consistency.md) and the reproducibility advice above. The cost of bf16 on GPUs without native bf16 support (some older cards emulate it) was not checked here. Related: [quantized-large-vs-small-model](quantized-large-vs-small-model.md).
