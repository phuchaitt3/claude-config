---
topic: llm-model-comparison-with-judge
area: Research methods
question: How do you fairly compare two LLMs (a smaller and a larger one) on the same writing or generation task, and is a third model used as judge standard practice?
checked: 2026-11-24
review_months: 12
status: current
---
# Comparing two LLMs on one generation task: same brief, blind pairs, a judge checked against a person

- **Question:** To decide which of two models to use for producing a document (for example a study page), is it standard to give both the same brief in fresh sessions, then have a third model judge the outputs, and how is such a comparison kept fair?
- **Why separate:** findings/llm-judge-vs-em-f1 covers scoring QA answers and findings/llm-testset-cross-family-review covers building test sets; this entry is about choosing between two generator models.
- **Finding:**
  - **A judge model for pairwise comparison is standard.** Zheng et al. (NeurIPS 2023) is the base reference; it reports strong judges agreeing with humans about as often as humans agree with each other, and lists position, verbosity and self-enhancement bias (see findings/llm-judge-vs-em-f1 for the numbers). Pairwise judging (A against B) is a common design alongside direct scoring.
  - **Swap the order and call a tie when the two verdicts disagree.** Studies check position bias by running the judge twice with the candidates swapped; the MT-Bench study (400 items) treats disagreement between swaps as a tie. The effect depends on the judge: swapping significantly helped one model (+4.7 points) and not others, and on adversarial items it hurt all models tested. An explicit tie option is recommended so the judge does not invent a winner.
  - **A single judge run is noisy; repeat it.** Rating Roulette (arXiv 2510.27106) reports low agreement of a judge with itself across runs. A code-evaluation study (arXiv 2606.00920) finds two to three repeated runs enough to estimate the variance parts in its setup. A benchmark paper (arXiv 2606.13111) reports between-judge variance 2 to 4 times the within-judge variance, so the choice of judge matters more than re-running one judge. A 2026 AACL paper argues verdicts should be tested under repeated sampling, position swaps and format changes, not only agreement.
  - **Check the judge against a person on a subset.** Validate against labels collected independently of the judge; report agreement with a bootstrap confidence interval; agreement is high on clear pairs and low on close ones, where people also disagree.
  - **A judge from a different family from both candidates is the recommended mitigation for self-preference** (findings/llm-testset-cross-family-review; the size of the bias is disputed).
  - **Matched settings.** Compare models at the same effort or reasoning level (findings/agent-model-effort-selection: "compare models only at matched effort").
  - **No source gives a sample size** for how many pairs a model comparison needs; pick it from the confidence-interval width (findings/eval-sample-size).
  - **(inference: findings/llm-model-comparison-with-judge)** For one document, the comparison has n = 1: a single pair cannot show a model is better, only whether the output meets named criteria. Criteria that can be checked mechanically (every code line commented, a trace present, no ASCII picture) are more reliable than a judge's opinion, and the intended reader's own blind reading is the ground truth. A judge from the same family as one candidate may lean toward it; with Anthropic models only, a judge from the third model tier (or the reader) avoids pairing a candidate with its own family.
- **Evidence strength:** *common practice* for pairwise judging, position swapping and checking a judge against people (several independent preprints agree); *single source* for each numeric figure (400 items, +4.7 points, two to three runs, 2 to 4 times). No study found that compares two writer models on producing study material.
- **Sources:**
  - Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", NeurIPS 2023 (peer-reviewed): https://arxiv.org/abs/2306.05685
  - "Judging the Judges: A Systematic Evaluation of Bias Mitigation Strategies in LLM-as-a-Judge Pipelines", arXiv 2604.23178 (preprint): https://arxiv.org/pdf/2604.23178
  - "Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge", arXiv 2406.07791 (preprint): https://arxiv.org/html/2406.07791v9
  - "Rating Roulette: Self-Inconsistency in LLM-As-A-Judge Frameworks", arXiv 2510.27106 (preprint): https://arxiv.org/html/2510.27106
  - "How Much Can Repeated Running Buy? A Measured Variance Ceiling for LLM Code Evaluation", arXiv 2606.00920 (preprint): https://arxiv.org/pdf/2606.00920
  - "Same Input, Different Scores: A Multi Model Study on the Inconsistency of LLM Judge", arXiv 2603.04417 (preprint): https://arxiv.org/abs/2603.04417
  - MOVE, a German public sector benchmark, arXiv 2606.13111 (preprint, source of the 2 to 4 times figure): https://arxiv.org/pdf/2606.13111
  - MLflow, "Pairwise LLM Evaluation: How to Compare Model Outputs Fairly" (vendor guide): https://mlflow.org/articles/pairwise-llm-evaluation/
- **Limits:** two standard searches; pages were read through search summaries, not in full, so the figures are as the summaries gave them and the version of each preprint was not checked. The numeric figures come from single studies on other tasks (chat preferences, code evaluation, a German benchmark), not on study-page writing. No source specifies a number of pairs.
- **Checked:** 2026-11-24
