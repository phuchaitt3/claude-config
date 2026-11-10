# Confidence intervals in RAG and retrieval evaluation

- **Question:** Do practitioners and researchers report confidence intervals (bootstrap) for RAG or retrieval test results, and is it worth it on a small set compared with writing more questions?
- **Finding:**
  - **Yes, in IR research and increasingly in RAG evaluation.** Bootstrap intervals for retrieval metrics go back to IR evaluation work (Cormack and Lynam, SIGIR 2006; Soboroff, EVIA 2014). RAG frameworks report them: ARES gives intervals via prediction-powered inference from a small human-labelled set; VERA bootstraps its metrics (2.5th–97.5th percentiles). A 2026 study of a documentation RAG assistant found most "winner vs runner-up" rankings did not survive a paired bootstrap (3 of 6 held).
  - **What it measures:** sampling noise (how much the score would move with another set of questions of the same kind), not bias. It cannot fix a skewed question set (for example synthetic questions that copy the text); only better questions fix that.
  - **Cheap, and it tells you whether you need more questions.** The bootstrap costs seconds of compute. Its width tells you whether the set is big enough to separate two designs; more questions narrow it (roughly with the square root of the count).
  - **Comparisons use a paired bootstrap** (both systems on the same resampled questions); a difference whose interval includes 0 is unproven. Non-overlapping separate intervals are only a rough test.
  - **Clustered questions** (several from one document) make a plain bootstrap too narrow; resample clusters instead. Bootstrap needs roughly n ≥ 30, ideally 50+.
- **Sources:**
  - ARES, arXiv 2311.09476 (research paper): https://arxiv.org/pdf/2311.09476
  - VERA, arXiv 2409.03759 (research paper): https://arxiv.org/pdf/2409.03759
  - Reliable confidence intervals for IR evaluation using generative AI, arXiv 2407.02464 (research paper): https://arxiv.org/pdf/2407.02464
  - Cormack, statistical precision of IR evaluation (research, author page): https://cormack.uwaterloo.ca/sigirboot
  - Soboroff, EVIA 2014 (workshop paper): https://research.nii.ac.jp/ntcir/workshop/OnlineProceedings11/pdf/EVIA/04-EVIA2014-SoboroffI.pdf
  - NeurIPS 2026 poster on paired bootstrap in RAG comparisons (conference page): https://neurips.cc/virtual/2026/178387
  - DEV Community, eval CIs assume independent examples (practitioner post): https://dev.to/maya_andersson_dev/your-evals-confidence-interval-assumes-independent-examples-yours-are-clustered-292c
- **Limits:** Read through search summaries; the NeurIPS item and several RAG papers are recent and not checked in full. How often industry teams report intervals (as against research) was not measured.
- **Checked:** 2026-11-10
