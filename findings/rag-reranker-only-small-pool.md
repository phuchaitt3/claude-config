# Cross-encoder over every chunk, with no first-stage retriever

- **Question:** Is it established practice to skip first-stage retrieval (BM25, dense, hybrid) and score every chunk with a cross-encoder reranker, and when does that fit?
- **Finding:**
  - **The two-stage design exists only for cost.** Retrieve-then-rerank uses a cheap retriever to narrow a large collection, because scoring "thousands or millions" of query-document pairs with a cross-encoder is too slow; the retriever's set is "e.g. 100" candidates (Sentence Transformers docs). Vendor and tutorial guides put the reranked pool at about 20-100, up to a few hundred, and recommend a cross-encoder when there are under about 100 candidates per query and ranking accuracy matters most. So when the whole pool is already that small (for example one document's chunks in single-document QA), scoring every chunk is the reranking stage applied to all candidates, not a departure from it.
  - **Same pattern in reading comprehension.** Answer-sentence selection and evidence selection score every sentence or paragraph of the given passage against the question with a cross-attention model and keep the top ones; that is the standard setup for single-document QA, where there is nothing to retrieve from.
  - **Recall argument for it:** a reranker can only reorder what the first stage hands it, so scoring all chunks removes first-stage misses. A hybrid stage adds nothing if its union already returns every chunk.
  - **Caveat, more is not always better:** Jacob et al. (arXiv 2411.11767, ReNeuIR workshop at SIGIR 2025) found that the best rerankers improve at first as they score more documents, then decline and can fall below the retriever, including "phantom" high scores for unrelated documents. Their pools run to full collections, far above tens of chunks; the checker's inference is that a pool of tens of chunks from one relevant document sits in the safe range, but that is not measured.
  - **"Reranker beats the hybrid" is not automatic:** whether scoring all chunks with the reranker beats a fused or hybrid ranking is an empirical question per dataset; claim it only with an ablation.
- **Sources:**
  - Sentence Transformers, "Retrieve & Re-Rank" (official docs): https://www.sbert.net/examples/applications/retrieve_rerank/README.html
  - Jacob, Lindgren, Zaharia, Carbin, Khattab, Drozdov, "Drowning in Documents: Consequences of Scaling Reranker Inference", arXiv 2411.11767 (research paper; abstract read, full paper not): https://arxiv.org/abs/2411.11767
  - Mixpeek, rerank stage docs (vendor docs, pool sizes and latency): https://docs.mixpeek.com/retrieval/stages/rerank
  - The Neural Base, cross-encoder vs bi-encoder reranking (tutorial): https://theneuralbase.com/compare/cross-encoder-vs-bi-encoder-reranking/
  - Answer sentence selection with cross-encoders, arXiv 2205.10455 (research paper; summary only); sentence selection for multi-choice reading, arXiv 1908.11511 (research paper; summary only)
- **Limits:** Pool sizes come from vendor docs and tutorials, not benchmarks, and depend on model size and hardware. No study was read that compares "rerank every chunk" against hybrid-then-rerank on single-document QA. The reading-comprehension papers were seen through search summaries only.
- **Checked:** 2026-11-10
