# Tuning on the test set, and what research practice does instead

- **Question:** Is it acceptable to choose hyperparameters on the same samples a result is reported on, and what is the accepted practice in ML/NLP research?
- **Finding:**
  - Choosing settings by their score on a finite sample, then reporting the score on that same sample, is optimistically biased. Cawley and Talbot show that this over-fitting in model selection is often about as large as the differences between the methods being compared, so it cannot be ignored in a comparison (JMLR 2010).
  - Accepted practice is a three-way split: tune on a validation (dev) split, then evaluate once on a test split that nothing was chosen on. With little data, use nested cross-validation (an inner loop picks settings, an outer loop estimates performance).
  - Tuned settings can depend on how the data is split, so reliable selection needs several splits or repeated cross-validation (Moss, Leslie and Rayson).
  - Reporting norms (NLP Reproducibility Checklist): the hyperparameter bounds searched, the number of trials, the selection method and criterion, the splits used, and variance or summary statistics. Dodge et al. (2019) add that test scores alone are not enough to say which method is best, and recommend reporting expected validation performance as a function of the tuning budget.
  - Comparing two systems on the same test set uses a paired significance test (Dror et al., ACL 2018, with a protocol for choosing the test). *Checker's inference, not confirmed in these sources:* for per-sample F1, a paired bootstrap or a permutation test is the usual choice.
  - *Checker's inference:* when a proposed method has more tuned settings than its baselines, tune every method under the same budget on the same dev split. Otherwise the comparison favours the method that was tuned most.
- **Sources:**
  - Cawley and Talbot, "On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation", JMLR 11 (2010) (peer-reviewed): https://www.jmlr.org/papers/v11/cawley10a.html
  - Dodge et al., "Show Your Work: Improved Reporting of Experimental Results", EMNLP 2019 (peer-reviewed): https://arxiv.org/abs/1909.03004
  - NLP Reproducibility Checklist v1.2, used at EMNLP and ACL (community standard): https://maxx-css.github.io/jesse/NLP_Reproducibility_Checklist_V1.2.pdf
  - Moss, Leslie and Rayson, J-K-fold cross-validation in NLP (peer-reviewed; ACL Anthology author page): https://aclanthology.org/people/henry-moss/
  - Dror et al., "The Hitchhiker's Guide to Testing Statistical Significance in NLP", ACL 2018 (peer-reviewed): https://aclanthology.org/P18-1128/ ; appendix: https://arxiv.org/abs/1809.01448
- **Limits:** found through search summaries; the full texts were not read. The search did not confirm which test Dror et al. recommend for F1 specifically. A blog post that turned up in the search was not used.
- **Checked:** 2026-11-08
