---
topic: inference-time-vs-finetuning-gain
area: Research methods
question: Is it normal for a training-free inference-time method to give a smaller gain than fine-tuning, and is reporting it on top of a fine-tuned model standard practice?
checked: 2026-11-19
review_months: 12
status: current
---
# Inference-time method versus fine-tuning: relative gain size

- **Question:** A training-free, inference-time method (a decoding or attention edit) is applied on top of a fine-tuned model. Is a gain much smaller than the fine-tuning gain normal, and does reporting both make the method look weak?
- **Finding:**
  - **No source found that measures it.** Two searches (2026-11-19) found no paper that states how large an inference-time gain on a fine-tuned checkpoint is relative to the fine-tuning gain, and no hiring-side source on how a reader perceives the two numbers together.
  - **Stacking is described as a normal and complementary use.** One preprint on a training-free decoder says its method is complementary to supervised fine-tuning, RLHF and DPO, and operates on a frozen model's distribution rather than replacing training. Summaries of contrastive decoding describe it as complementary to prompting and fine-tuning. These are the authors' own claims (preprints, read as search summaries).
  - **Training-free methods are normally compared with other training-free methods**, because cost is part of the comparison (see `findings/research-improvement-size`). Several training-free RAG-noise papers in the results compare only against other training-free baselines; the one that argues against fine-tuning pipelines (a neuron-editing method) is an adjacent method, not an attention edit.
  - *Checker's inference:* fine-tuning on in-domain data typically moves a small model far more than a decoding or attention edit does, because it changes the weights for the task. A method that adds a few points on top of an already fine-tuned model shows that its gain survives a stronger baseline, which is the stronger claim; the smaller size beside the fine-tuning number is expected, not a weakness. A reader who compares the two numbers without the cost difference (training versus none) may still read the small one as small, so a bullet that shows both should say the method needs no training. `(inference: findings/inference-time-vs-finetuning-gain)`
- **Evidence strength:** *no direct source*; adjacent preprints and one course report (weak). The finding rests on the inference line above.
- **Sources:**
  - [Energy-based decoding, preprint 2605.28020 (summary pages)](https://www.alphaxiv.org/abs/2605.28020): training-free decoding stated to be complementary to SFT, RLHF and DPO (authors' claim, not checked against the paper).
  - [Contrastive decoding for reasoning (paper summary)](https://academy.dair.ai/papers/contrastive-decoding-for-reasoning): described as complementary to prompting and fine-tuning.
  - [Inference-time techniques for code generation (University of Washington course report)](https://courses.cs.washington.edu/courses/cse503/25wi/final-reports/Inference-Time%20Techniques%20for%20Efficient%20Code%20Generation.pdf): a student report; weak.
  - [Adaptive Contrastive Decoding in RAG for noisy contexts, Findings of EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.136.pdf), through `findings/research-improvement-size`: gains of a few points are reported for such methods.
  - [Grft, trained representation intervention (arXiv 2502.14100)](https://web3.arxiv.org/pdf/2502.14100): its authors call training-free prompting methods unreliable, the other side of the argument.
- **Limits:** All read through search snippets, none in full. No stacking experiment (the same method with and without fine-tuning, with both gains reported) was found. Some results are AI-generated summaries of preprints. Nothing covers how recruiters or reviewers read a bullet that lists a large fine-tuning gain beside a small method gain.
- **Checked:** 2026-11-19
