# What retrieval scores to expect, and when a high one is suspect

- **Question:** Is a top-5 hit rate near 100% normal for RAG retrieval, or a sign of evaluation bias? What ranges are reasonable?
- **Finding:**
  - **There is no typical range.** Hit@k depends mostly on corpus size and on how the questions were made, so a figure means little without both. Reported values run from about 10–16% Hit@5 (BM25 and dense retrieval over a 500K-passage Wikipedia subset) to 100% (30 synthetic queries over 30 documents, which its authors called "a sanity check rather than a benchmark").
  - **Corpus size:** fewer candidates means higher scores. On HotpotQA, Recall@5 fell from 0.92 with a 10-passage pool to 0.69 with 100 passages.
  - **Question construction:** questions written by someone reading the passage share its words and are easier than real user queries. The DPR paper (Karpukhin et al., 2020) attributes BM25's lead on SQuAD to annotators writing questions after seeing the passage, which gives exact-match search "an unnatural and unfair advantage" (Lin et al., text-ranking survey). Synthetic queries flatter retrievers: one study found Hit@5 dropped 29–37 points from synthetic to authentic queries, the best synthetic configuration dropping most. See also [rag-retrieval-eval-without-benchmark](rag-retrieval-eval-without-benchmark.md) (synthetic sets rank retrievers well but overstate absolute quality).
  - **Signs a high score is an artifact rather than skill:** a small or curated candidate pool that is smaller than the deployed one; questions sharing most of their words with the gold passage; leakage (the question, or a near-copy, indexed); training data that overlaps the test set; tiny sets (30 questions give about ±5 points of noise).
  - *Checker's inference:* a high score is honest when the evaluation's search space equals the deployed one (e.g. retrieval restricted to one book in both) and the set is held out, leak-checked and reported with intervals. It then measures an easy task faithfully; the claim should say what the task was (corpus size, how questions were made), and a harder set (paraphrased or real queries) gives the realistic figure.
- **Evidence strength:** research papers for the SQuAD lexical-overlap effect and the pool-size effect; single studies for the synthetic-vs-authentic drop; *no data found* for a field-wide typical range.
- **Sources:**
  - Karpukhin et al., Dense Passage Retrieval (research paper; search summary): https://arxiv.org/pdf/2004.04906
  - Lin, Nogueira, Yates, Pretrained Transformers for Text Ranking (survey; search summary): https://arxiv.org/pdf/2010.06467
  - Beyond Benchmark Scores: synthetic and authentic query distributions in RAG evaluation (arXiv preprint; search summary): https://arxiv.org/pdf/2609.14579
  - EnterpriseRAG-Bench (arXiv preprint; search summary): https://arxiv.org/pdf/2605.05253
  - Tell Me, mental well-being assistant with RAG (arXiv preprint, the 30-document sanity check; search summary): https://arxiv.org/pdf/2511.14445
  - Retrieval utilization across model scale (arXiv preprint, 500K-passage figures; search summary): https://arxiv.org/pdf/2603.11513
  - BGE-M3 fine-tuning data README (official dataset card; lists no Vietnamese set): https://huggingface.co/datasets/Shitao/bge-m3-data/blob/main/README.md
- **Limits:** All read through search summaries; the HotpotQA pool and 500K-passage figures were not traced to the exact paper pages. The synthetic-vs-authentic drop is one preprint. No source gives ranges for Vietnamese or for single-book corpora. Training-data overlap for bge-reranker-v2-m3 was not checked.
- **Checked:** 2026-11-13
