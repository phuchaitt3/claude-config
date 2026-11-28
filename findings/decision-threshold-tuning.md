---
topic: decision-threshold-tuning
area: ML systems
question: How should a score cut-off (abstain, relevance filter) be chosen and stored, instead of a hand-picked hard-coded number? (Separate entry: no other entry covers thresholds or hyperparameters.)
checked: 2026-11-28
review_months: 12
status: current
---
# Choosing a decision threshold

- **Question:** How to choose and keep a score cut-off?
- **Finding:**
  - Pick the threshold on validation (or calibration) data, apply it to separate test data (research preprints; conformal prediction tutorial).
  - A threshold tuned on one data distribution may not transfer to another (label-shift paper).
  - Reranker docs: gather scores on 30 to 50 representative queries of your own domain to set a cut-off; scores are not calibrated probabilities (Cohere docs).
  - A fixed score cut-off must be re-calibrated when the scoring model changes (Pinecone docs).
  - Inference (checker's): a measured number written as a configurable default, with the script, data split and model recorded beside it, is not "hand-picked"; the risk is the model changing while the number stays, so tie the two (a test, or a note at the setting).
- **Sources:**
  - https://arxiv.org/pdf/2107.07511
  - https://arxiv.org/pdf/1802.07024
  - https://docs.cohere.com/docs/reranking-best-practices
  - https://docs.pinecone.io/guides/search/rerank-results
- **Limits:** read through search summaries. No source found on where in code or config to store a threshold.
- **Evidence strength:** moderate for tune-on-validation and re-calibrate-on-model-change; none for storage.
