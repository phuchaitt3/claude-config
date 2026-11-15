---
topic: agent-model-effort-selection
area: Agent setup
question: How reliable is an agent's own judgement of which model and effort a task needs, and what does the vendor advise for choosing between a smaller and a larger model?
checked: 2026-11-15
review_months: 6
status: current
---
# Agent judgement of model and effort per task

**Question:** How reliable is a coding agent's judgement of which model (smaller or larger) and effort level a task needs, and what does Anthropic advise for the choice?

**Finding:**

- **Vendor advice (Anthropic, Claude Code, 2026-07-07):** "Choose smaller models for more routine tasks and larger models for more complex or ambiguous tasks." Routine means precisely described edits, mechanical changes, or questions about code already in context. Hard means subtle bugs, unfamiliar domains, or architecture decisions. Use the model's default effort for most tasks and treat effort as "a general preference rather than a task-by-task decision". Check context and scoping first. If Claude had the right context, clearly tried and was still wrong, move to a larger model. If the work on a larger model is routine, drop to a smaller one. On hard multi-step tasks a larger model may finish in fewer steps, so it can cost less per task despite a higher price per token, and it can finish tasks a smaller model cannot finish at any effort. The article does not describe the agent choosing its own model.
- **Agents overrate their own chance of success.** Every LLM tested by Barkan et al. (2025-12) was overconfident about its own success. Most predicted it better than chance. Larger or newer models did not discriminate better, except Claude models, which showed an improving trend. Reasoning models were no better. Overconfidence grew as agentic tasks went on. In-context records of past failures reduced it for some models but not all.
- **Coding agents specifically:** Kaddour et al. (2026-02) found overconfidence in every setting tested, for example one agent that succeeded 22% of the time predicted 77%. A prediction made before execution discriminated successes from failures at least as well as a review after execution, though the difference was not always significant. Framing the self-assessment as bug-finding gave the best calibration.
- **Routing research:** learned routers trained on outcome or preference data beat random routing. RouteLLM reports more than 2x lower cost at little quality loss on MT Bench, MMLU and GSM8K. When a model judges a query's difficulty itself, the work reports results that are useful but imperfect. Papers note that the difficulty estimate, not the router design, is the main bottleneck, and probes on internal activations often do better than asking the model.
- **(inference: findings/agent-model-effort-selection)** Since agents overrate their own success, an agent asked "does this need the larger model?" will more often answer "no" than the outcome justifies. A rule that also puts the burden of proof on the larger model adds to that lean. The sources do not test this combination directly.

**Evidence strength:** *vendor or single source* for the Anthropic guidance. *Common practice* for "LLM agents are overconfident about their own success": several independent preprints agree. No study measures how well an agent picks between models for its own coding tasks.

**Sources:**

- [Anthropic: Choosing a Claude model and effort level in Claude Code](https://claude.com/resources/articles/claude-model-and-effort-level-in-claude-code), 2026-07-07 (vendor docs/blog); linked from [Claude Code model configuration docs](https://code.claude.com/docs/en/model-config.md) (official docs).
- [Barkan, Black, Sourbut: Do Large Language Models Know What They Are Capable Of? (arXiv 2512.24661)](https://arxiv.org/abs/2512.24661) (preprint).
- [Kaddour et al.: Agentic Uncertainty Reveals Agentic Overconfidence (arXiv 2602.06948)](https://arxiv.org/abs/2602.06948) (preprint).
- [Act or Escalate? (arXiv 2604.08588)](https://arxiv.org/html/2604.08588) (preprint): miscalibration makes models act when they should escalate, or the reverse; behaviour varies by model.
- [RouteLLM (arXiv 2406.18665)](https://arxiv.org/abs/2406.18665), [LMSYS blog](https://lmsys.org/blog/2024-07-01-routellm) (paper and its authors' blog).
- [DiSRouter (arXiv 2510.19208)](https://arxiv.org/pdf/2510.19208), [difficulty probes (arXiv 2511.03808)](https://arxiv.org/html/2511.03808), [probe reliability on long reasoning (arXiv 2602.09924)](https://arxiv.org/pdf/2602.09924) (preprints): self-routing and difficulty estimation.

**Limits:** the research items are preprints, mostly on math and coding benchmarks; none checked for peer review. Only the abstracts of the two overconfidence papers were read, so their numbers are limited to what the abstracts give. No source studies a subscription plan's usage limits, or how much a failed first attempt on the smaller model costs before escalating. The Anthropic article targets current models and may change with each model release.

**Checked:** 2026-11-15
