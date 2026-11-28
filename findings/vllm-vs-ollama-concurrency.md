---
topic: vllm-vs-ollama-concurrency
area: ML systems
question: What difference should be expected between vLLM and Ollama under concurrent requests, including on a T4 with quantized weights? (Separate entry: vllm-gpu-requirements covers only which GPUs run it.)
checked: 2026-11-28
review_months: 6
status: current
---
# vLLM against Ollama under concurrent load

- **Question:** What should a comparison of the two servers expect at 1, 4 and 16 or more requests in flight?
- **Evidence strength:** one vendor benchmark (Red Hat, a vLLM contributor) for the direction; anecdotal for anything on a T4 or with AWQ weights.
- **Finding:**
  - Red Hat, one A100 40GB, Llama 3.1 8B, full-precision weights on both servers, vLLM 0.9.1 and Ollama 0.9.2: peak throughput 793 against 41 tokens/s, P99 latency at peak 80 ms against 673 ms. The page's text gives no figures for 1, 4 or 16 (graphs only). Ollama handles 4 parallel requests by default; the tuned run used `OLLAMA_NUM_PARALLEL=32`. Some blogs wrongly attribute these numbers to a T4.
  - Blogs and a 2026 paper report the same direction with very different sizes, and roughly equal results at one user.
  - On T4s, AWQ is not free speed: one small run with a 1.5B model found AWQ at 1.61 times fp16 throughput with one sequence and 0.50 times with 128 sequences (personal repository).
  - **Inference:** vLLM ahead of Ollama in aggregate throughput at 16 in flight is the expected direction; no source gives the size of the gap for AWQ against Q4_K_M on a T4 at a 3B model, so a measured result there is not predictable from these figures. XFORMERS attention on a T4 was not covered.
- **Sources:**
  - Red Hat, Ollama vs vLLM (vendor): https://developers.redhat.com/articles/2025/08/08/ollama-vs-vllm-deep-dive-performance-benchmarking
  - Benchmarking Ollama and vLLM for concurrent serving (journal paper, read as a search summary): https://www.mdpi.com/2076-3417/16/11/5435
  - vLLM on two T4s, AWQ and fp16 (personal repository): https://github.com/lyftium/vllm-serving-benchmark-t4
- **Limits:** only the Red Hat page was opened; the rest are search summaries. No official vLLM or Ollama comparison was found.
- **Checked:** 2026-11-28
