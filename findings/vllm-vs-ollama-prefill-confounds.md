---
topic: vllm-vs-ollama-prefill-confounds
area: ML systems
question: Which documented settings can hide vLLM's concurrency lead over Ollama on a T4-class (compute capability 7.5) GPU?
checked: 2026-11-28
review_months: 6
status: current
---
# vLLM against Ollama on older GPUs: confounds to control

- **Question:** Which documented settings can hide vLLM's lead under concurrency?
- **Finding:**
  - Ollama 0.40.13 runs llama-server and sends `cache_prompt: true`, so replaying the same prompts across load levels can reuse cached prefixes. vLLM 0.10.2 turns prefix caching and chunked prefill on by default in its V1 engine, not in V0.
  - `VLLM_ATTENTION_BACKEND=XFORMERS` is not a V1 backend name and falls back to V0; `XFORMERS_VLLM_V1`, or leaving it unset, keeps V1.
  - AWQ-Marlin needs compute capability 8.0, so a T4 uses the older AWQ kernel; vLLM's docs (0.4 to 0.7) call AWQ under-optimised.
  - Inference, untested: with long prompts and short answers such a test mostly measures prefill, and prompt reuse can reverse the ranking. Control it with a unique first line per request in both arms.
- **Sources:**
  - https://github.com/ollama/ollama/blob/v0.40.13/llm/llama_server.go
  - https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
  - https://github.com/vllm-project/vllm/tree/v0.10.2/vllm
  - https://docs.vllm.ai/en/v0.7.1/features/quantization/auto_awq.html
- **Limits:** configuration facts only; no source or run shows which of these caused any measured gap. llama.cpp README read from master, not the build Ollama pins. Source files were read by a research subagent.
