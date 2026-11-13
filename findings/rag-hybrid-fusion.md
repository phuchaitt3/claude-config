# Merging vector and keyword results in hybrid search

- **Question:** How do hybrid search systems merge vector (dense) and keyword (sparse, BM25 or full-text) results, and is Reciprocal Rank Fusion (RRF) the default?
- **Finding:**
  - **Two families.** Rank-based fusion (RRF: each result scores the sum of 1/(k + rank) over the lists it appears in, usually k = 60, from Cormack et al. 2009) uses only ranks. Score-based fusion normalises each list's scores (min-max, z-score, L2) and takes a weighted sum (often an `alpha` between keyword and vector).
  - **RRF is the common starting point, not a universal default.** Azure AI Search applies RRF to every hybrid query; Elasticsearch offers an `rrf` retriever (rank constant 60) and a linear one; OpenSearch has a normalisation processor (weighted sum) and a later RRF score-ranker; Weaviate defaults to relative score fusion (min-max, weighted) since v1.24.
  - **Why RRF first:** BM25 and cosine scores are on different scales, so a raw weighted sum is fragile; RRF needs no normalisation and no tuning. **Why weighted later:** with an evaluation set showing one signal should dominate, a tuned weighted sum can beat RRF. Guides: start with RRF, confirm hybrid beats each signal alone, move to weights only with evaluation data.
- **Sources:**
  - BigData Boutique, RRF: how it works and when to use it; hybrid search fusion methods compared (consultancy blog): https://bigdataboutique.com/blog/reciprocal-rank-fusion-how-it-works-and-when-to-use-it , https://bigdataboutique.com/blog/hybrid-search-fusion-methods-compared
  - Digital Applied, hybrid search BM25 + vector + reranking reference 2026 (vendor guide): https://www.digitalapplied.com/blog/hybrid-search-bm25-vector-reranking-reference-2026
  - Jacar, hybrid search: combining BM25 and vectors seriously (blog): https://jacar.es/en/hybrid-search-combining-bm25-and-vectors-seriously/
  - Cormack, Clarke, Büttcher, "Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods", SIGIR 2009 (research paper; cited, not re-read).
- **Limits:** Engine defaults were read through third-party summaries, not each vendor's current docs, and they change between versions. No head-to-head study of RRF against tuned weights was read.
- **Checked:** 2026-11-10
