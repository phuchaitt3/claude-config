---
topic: model-size-during-development
area: ML systems
question: When building an LLM app, should development start on a small model and swap up later, or start on the most capable one? (Separate entry: other model-choice entries cover agent models and quantized sizes.)
checked: 2026-11-28
review_months: 6
status: current
---
# Model size while developing an LLM app

- **Question:** Start small and upgrade, or start capable and step down?
- **Evidence strength:** two vendors' own model-selection pages; blogs of uneven quality beside them.
- **Finding:**
  - Anthropic describes both as valid: efficiency-first (start with the smallest model, upgrade only if necessary) and capability-first (start with the most capable, then optimise); it says most workloads start with its large model.
  - OpenAI advises starting most API work on a mid-to-large model, using the small one for small repeatable tasks, and keeping the lightest setting that meets the quality bar on the same inputs.
  - The common condition is an evaluation with a quality bar that is run again whenever the model changes (both vendor pages and blogs).
  - **Inference:** a small model is fine for exercising the pipeline; prompts, citation format and refusal behaviour tuned on it still need checking on the model that ships, and reported quality figures belong to the model that produced them.
- **Sources:**
  - Anthropic, choosing a model (official docs): https://platform.claude.com/docs/en/about-claude/models/choosing-a-model
  - OpenAI, model selection (official docs): https://developers.openai.com/api/docs/guides/model-selection
- **Limits:** both vendors sell hosted models; neither addresses self-hosted models under 1B parameters.
- **Checked:** 2026-11-28
