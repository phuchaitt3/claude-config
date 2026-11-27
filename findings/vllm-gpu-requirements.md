---
topic: vllm-gpu-requirements
area: ML systems
question: Which GPUs can run vLLM, and does that include older consumer cards such as the GTX 10 and 16 series?
checked: 2026-11-27
review_months: 6
status: current
---
# vLLM GPU requirements

- **Question:** Can vLLM run on a GTX 1060 or a GTX 1660 Ti?
- **Evidence strength:** the vendor's installation pages, read as search-result summaries only; card compute capabilities are the checker's own knowledge.
- **Finding:**
  - The newest installation page requires Linux and a GPU of compute capability 7.5 or higher (examples: T4, RTX 20xx, A100, L4). Pages around v0.7.x said 7.0 or higher.
  - Windows is not supported natively (WSL or a community fork).
  - **Inference:** a GTX 1060 (Pascal, 6.1) is below the minimum. A GTX 16xx card (Turing, 7.5) meets the stated number, but the pages do not name it, and 6 GB is tight for a language model.
- **Sources:**
  - vLLM GPU installation (official): https://docs.vllm.ai/en/v0.28.0/getting_started/installation/gpu/
  - vLLM GPU installation, v0.7.2 (official): https://docs.vllm.ai/en/v0.7.2/getting_started/installation/gpu/index.html
- **Limits:** nothing was run; the pages were not opened in full.
- **Checked:** 2026-11-27
