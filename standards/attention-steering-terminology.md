# "Attention steering" vs "attention intervention"

- **Question:** For an inference-time method that changes a language model's attention scores (e.g. adds a bias to pre-softmax logits to up- or down-weight chosen context tokens), is "attention steering" or "attention intervention" the more correct and recognised term?
- **Finding:**
  - "Attention steering" is the established name for this family. PASTA ("Tell Your Model Where to Attend: Post-hoc Attention Steering for LLMs", Zhang et al., ICLR 2024) coined it for up-weighting the attention scores of chosen tokens and down-weighting the rest at selected heads, at inference, with no weight updates. Follow-ups (AutoPASTA; "Spotlight Your Instructions") keep the term for reweighting attention toward or away from spans.
  - "Intervention" is the broader umbrella: any inference-time change to internal activations (e.g. Inference-Time Intervention, which shifts head activations rather than attention scores). Some RAG papers call their method an "inference-time attention intervention" (CoDA, ACL Findings 2026), so the phrase is correct but less specific.
  - *Checker's inference:* a method that edits attention logits or weights toward or away from context tokens is attention steering, and that is the more searchable, recognisable term. "Intervention" is not wrong and suits a general description. One document should use one term for one method, or define the second as the same thing, so a reader does not take them for two techniques.
- **Sources:**
  - Zhang et al., "Tell Your Model Where to Attend: Post-hoc Attention Steering for LLMs", ICLR 2024 (peer-reviewed): https://arxiv.org/abs/2311.02262 , https://proceedings.iclr.cc/paper_files/paper/2024/hash/b99d6cc40b05809c3d84b57a165448cd-Abstract-Conference.html
  - "Pay Attention to What You Need" (Scaled ReAttention), arXiv 2307.13365 (preprint): https://arxiv.org/abs/2307.13365v3
  - CoDA, "Intervention for Mitigating RAG Hallucinations", Findings of ACL 2026 (peer-reviewed): https://aclanthology.org/2026.findings-acl.576.pdf
- **Limits:** Read through abstracts and search summaries. Usage is a matter of convention in recent papers, not a glossary from a standards body. No count of term frequency was made.
- **Checked:** 2026-11-11
