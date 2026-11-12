---
name: model-effort
description: Load when picking or justifying a model and effort for a task, or when tagging a proposed next step. The table mapping task types to Sonnet or Opus and effort level.
---

# Model and effort table

Moved out of the always-loaded working rules on 2026-11-12 (user's decision, to cut start-up context); the text is unchanged. The one-line tag rule stays in the working rules.

| Task | Model, effort |
|---|---|
| Inbox and handoff updates, commits, merges, routine runs, logs | Sonnet, low |
| Small well-specified edits, tests for existing behaviour, lint | Sonnet, medium |
| New features, ports, schema changes, docs and reports; first-pass debugging | Sonnet, high |
| Bug unexplained after a Sonnet pass; bug needing several components held at once; open design question with a costly wrong answer (plan mode) | Opus, high (xhigh only if high failed) |
| Final wording of thesis, paper or public claims | Opus, high |
