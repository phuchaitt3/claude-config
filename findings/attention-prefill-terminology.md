---
topic: attention-prefill-terminology
area: Research methods
question: What do papers and docs call (a) the single last-position query that an inference-time method acts on, and (b) the fast built-in attention kernel the rest of the prompt runs through, and which wording avoids implying the custom part is slow?
checked: 2026-11-19
review_months: 12
status: current
---
# Wording for "last query row" and "fused SDPA attention" on a resume

- **Question:** A resume bullet says an attention-steering method (NNP) is applied only at the last query row of the prompt, while the rest of the prompt runs through PyTorch's fused attention. Which terms are standard, and does "optimized attention implementation" mislead?
- **Finding:**
  - **(a) The final position.** Papers on prefill speed-ups describe the same single-row computation as the *last prompt token's query* ("last-token query", "final prompt token's query", "last query row"); one notes that next-token prediction depends on the final hidden state; another aggregates over the *last n query positions*. The preprints say "last-token query" or "last query row"; neither is a fixed term of art. *Correction 2026-11-19:* this entry first called "last token" the more common plain form; no source showed "common", and "last token" alone can mean the last token of the prompt rather than its query row. The user chose "last query row", which also matches the thesis code (a row of `q`).
  - **(b) The rest of the prompt.** PyTorch's `scaled_dot_product_attention` (SDPA) is one call that dispatches to three backends: FlashAttention, memory-efficient attention and a "math" fallback; the fused kernels avoid materialising the full score matrix, which is why memory falls. The official wording is "fused kernels" for the first two; Hugging Face says SDPA "selects the fastest attention function" automatically. "SDPA" is the operation's name, not a speed claim.
  - *Checker's inference, wording:* "optimized attention (implementation)" implies the custom part is the unoptimized one and is vague about what is optimized; "fused" and "SDPA" are jargon for a first-time reader. The mechanism the reader can check against the result is memory: the fused path is *memory-efficient attention*, the name PyTorch itself gives one backend, and it explains "peak memory 2.9 to 1.2 GB". So "memory-efficient attention" describes the rest of the prompt without grading the steered part. Avoid "standard attention": in the literature it means the plain unfused version, the opposite of what ran.
  - *Checked in code, 2026-11-19:* the thesis hybrid path calls `F.scaled_dot_product_attention` with an explicit float mask, and its docs state the kernel that ran on the laptop benchmark (torch 2.1, GTX 1660 Ti): the memory-efficient kernel, not a fallback to the math kernel (thesis `docs/BENCH-BATCHING.md:98`, `attention.py` `_align_keys`). Checker's inference: FlashAttention would not take a float mask in torch 2.1. Not checked: T4 and other torch versions.
- **Evidence strength:** *documented behaviour* for the three SDPA backends (PyTorch blog and tutorial); *usage in papers* for "last-token query" (search summaries of preprints); *thesis code and docs* for the backend that ran; *no source* on how recruiters read either phrase.
- **Sources:**
  - [PyTorch blog, out-of-the-box acceleration](https://pytorch.org/blog/out-of-the-box-acceleration/): the three backends; fused kernels used when available.
  - [PyTorch SDPA tutorial](https://pytorch.org/tutorials/intermediate/scaled_dot_product_attention_tutorial): dispatch to FlashAttention or the C++ implementation.
  - [Hugging Face, attention interface](https://huggingface.co/docs/transformers/main/en/attention_interface): SDPA picks the fastest function.
  - [CLAA: Cross-Layer Attention Aggregation for LLM prefill](https://arxiv.org/pdf/2602.16054) and [Efficient LLM inference solution on Intel GPU](https://arxiv.org/pdf/2401.05391): last-token and last-n query positions; "customized SDPA kernel" (preprints; summaries only).
- **Limits:** Two standard searches, read through search-result summaries; the official `scaled_dot_product_attention` reference page was not retrieved. The last-token claims come from preprints, not a glossary. Nothing here is about resumes or hiring; the wording advice is the checker's inference. Related: findings/attention-steering-terminology (the method name).
- **Checked:** 2026-11-19
