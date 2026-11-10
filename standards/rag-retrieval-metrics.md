# Which metric to report for RAG retrieval

- **Question:** Is top-k hit rate (Hit@k) the standard single measure of retrieval quality, or should another metric lead?
- **Finding:**
  - **No single metric is enough**, but for first-pass RAG retrieval the usual headline is **Recall@k** at a k matched to how many chunks reach the model (5 or 10 is common): a generator can ignore a wrong chunk but cannot use a missing one.
  - **Hit@k** (did any relevant chunk reach the top k) is the most quoted RAG figure. With one relevant chunk per question it equals Recall@k; with several, it can look good while coverage is poor.
  - **MRR** (how high the first relevant chunk sits) is reported beside it to show ranking quality, and matters most when tuning rerankers. **nDCG@k** is for graded relevance labels.
  - Retrieval metrics are paired with answer metrics (correctness, faithfulness) for the whole system.
  - *Checker's inference:* on a resume, one retrieval number is enough if it is named plainly ("top-5 hit rate") and its k matches what the system feeds the model; MRR and the answer metrics belong in the interview.
- **Sources:**
  - Kunal Ganglani, RAG evaluation metrics for retrieval quality (practitioner blog): https://www.kunalganglani.com/blog/rag-evaluation-metrics-retrieval-quality
  - Future AGI, how to evaluate RAG systems (vendor guide): https://futureagi.substack.com/p/how-to-evaluate-rag-systems-the-complete
  - LayerLens, RAG evaluation framework for production (vendor blog): https://layerlens.ai/blog/rag-evaluation-framework-for-production-ai-systems
  - Hamel Husain, evaluate-RAG skill (practitioner material): https://kortix.com/marketplace/hamelsmu--evals-skills/evaluate-rag
  - See also standards/rag-retrieval-eval-without-benchmark (golden sets, synthetic questions).
- **Limits:** Practitioner and vendor sources, read through search summaries; no peer-reviewed comparison of metric choice was read.
- **Checked:** 2026-11-10
