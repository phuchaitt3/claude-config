# Can vLLM apply a custom, per-request bias to pre-softmax attention scores?

- **Question:** Can an inference-time method that adds a bias to pre-softmax attention scores, with token masks specific to each request, run inside vLLM, and what would it take?
- **Finding:**
  - **Fused kernels like FlashAttention and PagedAttention compute scores, softmax and weighting in one kernel**, so the scores are never exposed. Editing them used to mean a custom kernel (PyTorch FlexAttention blog: the "software lottery" of attention variants).
  - **FlexAttention removes that for pointwise edits.** A `score_mod(score, b, h, q_idx, kv_idx)` sees each pre-softmax score with its batch, head, query and key index and is compiled into one fused kernel. It can read tensors it closes over (for example `bias[q_idx][kv_idx]`), and changing their values does not recompile. Numerics are close to FlashAttention but not bitwise identical. It cannot see other scores in the row, so a bias that depends on row statistics does not fit.
  - **vLLM has a FlexAttention backend** (`vllm.v1.attention.backends.flex_attention`) with a paged KV cache and decoding. `FlexAttentionMetadata` has a `score_mod` field, wrapped so the user function gets *logical* query and key positions (converted from physical KV slots through the block table). The docs do not say who sets `score_mod` or how, and no request index is passed to it. Per-request data would need custom glue, such as a captured tensor indexed by physical KV slot.
  - **Custom backends are supported through plugins:** a platform plugin's `get_attn_backend_cls` returns the backend class (subclass of `AttentionBackend`), and since v0.13.0 `vllm.v1.attention.backends.registry.register_backend` adds one. No full example is given in the docs.
  - **No source found that runs an attention-steering method (for example PASTA, ICLR 2024) inside vLLM.**
  - **Checker's inference:** a constant bias on masked key positions of one query row is expressible as a `score_mod`, so the obstacle is engineering (per-request masks through the scheduler and paged cache, a per-layer strength, prefix caching, a custom backend), not the kernel. Expect numeric differences from an eager reference.
- **Sources:**
  - PyTorch, "FlexAttention: the flexibility of PyTorch with the performance of FlashAttention" (official blog, updated 2025-05-30): https://pytorch.org/blog/flexattention/
  - vLLM API docs, `flex_attention` backend (official): https://docs.vllm.ai/en/latest/api/vllm/v1/attention/backends/flex_attention/
  - vLLM plugin system (official docs): https://docs.vllm.ai/en/latest/design/plugin_system/
  - vLLM RFC on encoder/decoder feature compatibility (GitHub issue, older; says no backend fully supported custom bias then): https://github.com/vllm-project/vllm/issues/7366
  - PASTA, post-hoc attention steering (paper, ICLR 2024): https://arxiv.org/abs/2311.02262
- **Limits:**
  - Read from API docs, not from the vLLM source; how `score_mod` is populated, and whether the backend runs on every GPU (for example older ones such as T4), are unconfirmed.
  - vLLM's API changes between releases; recheck against the version in use.
- **Checked:** 2026-11-11
