# LLM-as-a-judge against exact match and F1 for QA answers

- **Question:** Does an LLM judge add anything over exact match (EM) and token F1 when scoring question-answering output, including extractive QA and RAG answers?
- **Finding:**
  - Yes, when the answers come from an LLM. Ho et al. (2025) scored LLM answers on four reading-comprehension datasets: correlation with human judgments rose from 0.22 (EM) and 0.40 (F1) to 0.85 with an LLM judge (v2 figures; v1 reported 0.17 and 0.36). They conclude EM and F1 underestimate LLM QA performance, because correct answers worded differently from the gold span lose credit. The judge was weaker on harder answer types but still beat EM and F1; they saw no self-preference bias in this task.
  - Strong judges agree with humans about as often as humans agree with each other (over 80% for GPT-4 on pairwise preferences, Zheng et al., NeurIPS 2023 Datasets and Benchmarks). The same paper lists position, verbosity and self-enhancement bias, and limited reasoning.
  - Judge scores depend on the judge model and vary between runs; practitioner guides recommend pinning the judge model, checking it against a human-labelled subset, and reading trends rather than absolute values (secondary sources, see Limits).
  - *Checker's inference:* EM and F1 stay the benchmark-native, deterministic and comparable numbers (SQuAD, UIT-ViQuAD report them), so the usual reporting is both: EM/F1 for comparability, plus a judge checked on a small human-labelled sample for answer correctness. A judge alone is not reproducible across judge models.
- **Sources:**
  - Ho, Huang, Boudin, Aizawa, "LLM-as-a-Judge: Reassessing the Performance of LLMs in Extractive QA", arXiv 2504.11972 (preprint; v3 dated 2026-05-29 not read): https://arxiv.org/abs/2504.11972
  - Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", NeurIPS 2023 (peer-reviewed): https://arxiv.org/abs/2306.05685
  - Practitioner guides on Ragas and judge drift (blog posts, secondary): https://machinelearningmastery.com/llm-evaluation-frameworks-compared-how-to-actually-measure-what-your-model-does/ ; https://dev.to/dublecc/rag-evaluation-metrics-guide-2026-faithfulness-context-precision-and-how-to-score-a-pipeline-46gi
- **Limits:** Ho et al. is one preprint with a modest human-annotated set, read from its abstract page; no independent replication found. Zheng et al. measures pairwise chat preferences, not QA correctness. No official Ragas documentation or peer-reviewed study of Ragas Factual Correctness itself was found. The judge-practice points come from blog posts only.
- **Checked:** 2026-11-09
