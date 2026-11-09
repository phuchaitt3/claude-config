# Evaluating RAG retrieval when no benchmark fits the use case

- **Question:** When no public benchmark matches a RAG system's documents and users (for example a low-resource language over long books), how do teams evaluate retrieval, and how far can LLM-generated test questions be trusted?
- **Finding:**
  - **A small golden set built from the system's own documents is the base.** Guides converge on a set of query → relevant-chunk pairs drawn from the real corpus, scored with Recall/Hit@k, MRR and nDCG, retrieval scored separately from generation so a failure can be placed. Suggested sizes vary (50–200 pairs, 100–300 questions); one guide warns that about 30 questions gives roughly 5 points of noise per run. The numbers are vendor rules of thumb, not measured standards.
  - **Real queries beat synthetic ones; synthetic ones fill the gap until real ones exist.** Sources call synthetic questions "a backstop, never the foundation": sample production logs (by intent, length, frequency, personal data stripped) as soon as there are users, tag synthetic entries, and feed failures (wrong-answer reports) back into the set.
  - **Synthetic questions rank retrievers reliably but flatter them.** In a controlled study (arXiv 2508.11758), GPT-4o-generated QA ranked retriever configurations in moderate-to-high agreement with human-written QA (Kendall τ up to 0.84), but did not rank generator models reliably, and every system scored lower on the human sets: synthetic questions are more specific and easier. Context precision agreed poorly (τ 0.08). So use synthetic sets to choose between retrieval designs, not to quote absolute quality.
  - **Filter synthetic questions.** Drop questions answerable without any retrieved context, and do not fine-tune an embedder on the same generated pairs used for testing (contamination).
  - **Without labels, reference-free LLM-judge scores** (context relevance, faithfulness) can run on sampled live traces, with periodic human review and drift monitoring. They complement a labelled set; recall still needs labels.
  - **Compare configurations with paired per-query tests** (or paired bootstrap), since metrics are means over a small set.
  - *Checker's inference:* questions written by someone reading the passage share its words, which favours lexical search (BM25); paraphrased or user-voice questions are the harder, more realistic test. Book-length English benchmarks exist (NovelQA: hand-written questions with evidence over novels of 200K+ tokens; RAGChecker reuses it for RAG by restricting retrieval to the question's novel); none was found for Vietnamese books. Vietnamese retrieval benchmarks found are general or legal (VN-MTEB, translated from MTEB; Zalo Legal 2021).
- **Sources:**
  - "Can we Evaluate RAGs with Synthetic Data?", arXiv 2508.11758 (research paper, read in full HTML): https://arxiv.org/html/2508.11758v2
  - Evidently AI, "A complete guide to RAG evaluation" (vendor guide): https://www.evidentlyai.com/llm-guide/rag-evaluation
  - Braintrust, "What is RAG evaluation?" and "RAG evaluation metrics" (vendor guides): https://www.braintrust.dev/articles/what-is-rag-evaluation , https://www.braintrust.dev/articles/rag-evaluation-metrics
  - "The Coverage Illusion", arXiv 2605.27220 (production case study; via search summary): https://arxiv.org/pdf/2605.27220
  - NovelQA, arXiv 2403.12766 (research benchmark): https://arxiv.org/abs/2403.12766 ; RAGChecker, arXiv 2408.08067 (research paper): https://arxiv.org/pdf/2408.08067
  - VN-MTEB, arXiv 2507.21500 (research benchmark): https://arxiv.org/html/2507.21500v1
- **Limits:** golden-set sizes and the log-sampling advice come from vendor blogs, not studies. The synthetic-data study used 94–100 human pairs per dataset, one generation method and GPT-4o as generator. Most other pages were read through search summaries. The search for Vietnamese book-length QA was two queries, so a dataset may exist that it missed.
- **Checked:** 2026-11-09
