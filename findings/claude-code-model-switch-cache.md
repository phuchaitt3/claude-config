---
topic: claude-code-model-switch-cache
area: Agent setup
question: Does switching models mid-session in Claude Code throw away the prompt cache and cost more tokens, and does changing effort do the same?
checked: 2026-11-21
review_months: 6
status: current
---

# Switching models and the prompt cache

- **Question:** Does switching models mid-session discard the prompt cache and raise token use?
- **Finding:**
  - Yes, for the next request. "Each model has its own cache. Switching models recomputes the entire request even when the content is identical"; the next request reads the whole conversation with no cache hits (Claude Code docs, "Actions that invalidate the cache", "Switching models"). Two requests share a cache only when model, speed and prefix match ("Cache scope").
  - The cost is one turn, not a lasting penalty: the new model writes its own cache on that turn and later turns hit it. Writes cost 1.25x (5-minute) or 2x (1-hour) the base input price; reads cost 0.1x, or 0.05x on Opus 5.5 and Sonnet 5.5, and 0.025x on Fable 5.2/5.1 (platform docs, "Pricing"). So a switch re-bills the whole history at the write rate instead of the read rate, once.
  - Effort level: on most models each effort level has its own cache too, so changing effort recomputes everything; with an API key or a Claude subscription this does not happen on Fable 5.1 and later, Opus 5.5, Sonnet 5.5 and Haiku 5.5. Bedrock, Google Cloud, gateways and HIPAA setups behave as on most models.
  - Related switches: each `opusplan` plan-mode toggle is a model switch; a skill's `model` frontmatter makes that turn a switch. A new subagent does not read the parent's cache on its first request (it has its own prompt and tools); a fork does, because it inherits the parent's prefix exactly.
  - Vendor advice: pick model and effort at the top of a session and save `/compact` for breaks between tasks; fewer mid-task changes give a higher hit rate. `/model` asks for confirmation only while the cache is still warm.
  - TTL in Claude Code: on a subscription within plan usage the main conversation gets a 1-hour cache; on an API key or usage credits, 5 minutes. Subagents and helper requests default to 5 minutes.
- **Evidence strength:** *official standard* (the tool vendor's own docs).
- **Sources:**
  - https://code.claude.com/docs/en/prompt-caching (official docs, read in full)
  - https://platform.claude.com/docs/en/build-with-claude/prompt-caching (official API docs; pricing and invalidation sections read, the last part of the page was truncated and not read)
- **Limits:**
  - Neither page says how cached versus uncached tokens count toward Pro or Max usage limits, so how much a switch costs against a subscription's limit is *no data found*. The API price multipliers show the relative cost, not the subscription's accounting.
  - Switching back to the earlier model within its TTL probably reads the old cache (caches are per model and the old entry is separate), but no page says so. (inference: findings/claude-code-model-switch-cache)
  - A third-party guide says the same about Opus to Haiku; not relied on (unofficial).
  - Model names, multipliers and exceptions change with each release; hence the 6-month review.
- **Checked:** 2026-11-21
