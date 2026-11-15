---
topic: llm-testset-cross-family-review
area: Research methods
question: When an LLM writes an evaluation set, is it standard to have a model from another family review it and a person check a sample, and does the cross-family step reduce bias?
checked: 2026-11-15
review_months: 12
status: current
---
# LLM-written test sets: generate, critique with another model, check a sample by hand

- **Question:** For a synthetic RAG or QA test set, is "one LLM writes the questions, a model from a different family reviews them, a person checks the flagged items and a control sample" industry practice, and does using a different family avoid bias?
- **Finding:**
  - **Generate, filter, then human-check a sample is the common pattern.** Questions are written from source passages, filtered by LLM critiques (groundedness, relevance, stands alone) or by a retrieval check (does the question retrieve its own passage), and a uniform sample is rated by people to measure how well the filter works. ARES, "Know Your RAG" (critiques run with Llama-3-70b) and ScIRGen (100-item expert sample; filter precision 89-95%) all follow it; a Microsoft guide calls the result a "silver" set refined into a "golden" one.
  - **A reviewer from another family is a recommended mitigation, not a settled requirement.** Self-preference bias is documented for LLM judges and extends to sibling models of the same family (Pombal et al., 2026, rubric-based evaluation), so practitioners advise a judge from a different lineage. An ICML 2026 paper argues most measured self-preference is an artefact of judge weakness on the task (no self-specific signature in 89.6% of reported cases). The evidence is about judges grading outputs; applying it to a reviewer checking generated questions is an inference.
  - **The human check should be measured, not token.** Sources check the LLM filter against human labels on a sample (ARES suggests about 150 or more annotated items for calibration). A handful of controls bounds the filter's miss rate only loosely.
  - **Real user questions should replace synthetic ones over time** (see findings/rag-retrieval-eval-without-benchmark).
- **Sources:**
  - ARES, arXiv 2311.09476 (research paper): https://arxiv.org/pdf/2311.09476
  - "Know Your RAG", arXiv 2411.19710 (research paper): https://arxiv.org/pdf/2411.19710
  - ScIRGen, arXiv 2506.11117 (research paper): https://arxiv.org/pdf/2506.11117
  - STELLAR-E, arXiv 2604.24544 (research paper): https://arxiv.org/html/2604.24544v1
  - Microsoft Data Science, "The path to a golden dataset" (practitioner blog): https://medium.com/data-science-at-microsoft/the-path-to-a-golden-dataset-or-how-to-evaluate-your-rag-045e23d1f13f
  - "Self-Preference Bias in Rubric-Based Evaluation of LLMs", arXiv 2604.06996 (research paper): https://arxiv.org/pdf/2604.06996.pdf
  - "Are LLM Evaluators Really Narcissists?", ICML 2026 (research paper): https://icml.cc/virtual/2026/poster/61230
  - LMArena, "Do blind battles reveal any bias?" (vendor blog): https://arena.ai/blog/llm-judge-self-preference/
- **Limits:** two standard searches; pages read through search summaries, not in full. No source names "different family for generator and reviewer" as a fixed standard for test-set building; that step rests on the judge self-preference literature, whose size is disputed. Sample-size figures come from single papers.
- **Checked:** 2026-11-15
