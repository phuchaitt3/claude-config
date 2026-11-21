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
  - When to switch (vendor blog, Aug 2026): "the start of a session or right after a /clear" are the cheap moments; the middle of a long conversation is the expensive one; "Run /clear between tasks." For a noisy repeated job, give a subagent its own definition with `model: haiku` (or sonnet) instead of switching the main session. The blog says this applies on a subscription too: "the same requests are what draw down your limits". The help center says "You can change models mid-session without losing your conversation" and defaults to Sonnet for most coding, Opus when stuck, Haiku for mechanical work, and `/clear` for a new task, `/compact` to continue a long one.
  - (inference: findings/claude-code-model-switch-cache) Following that advice, the practical rule is not "one model per session" but "switch at task boundaries, after `/clear`, or when the cache has already expired (idle longer than the TTL)", since the cost is one uncached turn.
- **Community practice (Reddit), *anecdotal*, read 2026-11-21** with the user's `webx` after finding URLs through the PullPush archive (`findings/reddit-access-for-agents`). Seven threads in r/ClaudeAI and r/ClaudeCode, Feb to Nov 2026 (two found later with `webx --reddit-search`); comment scores were not available, so nothing here is weighted by votes; no usernames kept.
  - A July 2026 post (about 40 comments in r/ClaudeAI, crossposted to three more subreddits) audited transcripts and put cache rewrites at about 30% of the poster's Fable use. It names "switching models mid-conversation (Fable to Sonnet to Fable)" as losing more than the switch saves, because caches are per model, and calls frequent effort switching "one of my worst habits". Replies: some commenters reported the same (usage "through the roof" after Sonnet to Fable and back); one asked whether two sessions on two models keep independent caches and a later reply said that workflow "significantly reduced" their token use; one doubted effort changes should break the cache. Fixes posted: one session per model with a notes file handed between sessions, `/compact` before a break, and keeping a session alive with a ping at the 55th minute of a 1-hour cache.
  - A May 2026 post (about 40-50 comments, r/ClaudeAI and r/ClaudeCode) lists `/model` among five cache busters and advises "Opus for planning, Sonnet for execution, but split them into separate sessions, not one session you keep flipping". A commenter objected that parts of it extrapolate API documentation to Claude Code and need verification.
  - A May 2026 thread (about 16 comments) asked about alternating Opus and Sonnet: replies describe switching to Opus for multi-file logic or subtle invariants, back to a cheaper model for execution, one saying the switch trigger should be measurable ("failed tests after 2 retries") rather than vague; one commenter runs Opus for everything on a Max plan.
  - A Feb 2026 post (about 20 comments) on cost says Claude Code applies model and effort to the whole session and per-step switching needs manual `/model`.
  - A Nov 2026 post says subagents left on Opus cost the poster about $1,600 over two months; setting `model: sonnet` in the subagent definition would have saved it, and commenters moved read-only subagents to the cheaper model.
  - Two Aug and Sep 2026 threads in r/ClaudeAI found by `webx --reddit-search` (about 24 and 15 comments, post scores 0 and 4): one asked whether switching re-reads the whole context (planning on one model, implementation on another). Replies: yes, caches are per model and per effort level, so after the cache lifetime a switch costs nothing extra (one reply: 5 minutes; another: 1 hour on the Max plan, which matches the docs); the usual advice was to write the plan or a handoff note to a file, then `/clear` or open a new session on the other model. The other asked whether it is safe to move a months-long project to a new model: replies said it is functionally safe, but a switch in the same session "breaks prompt caching and charges full price for the context" unless the cache has expired; some switch in-session routinely without problems and accept the cost; a hygiene tip was to tell the new model it was switched and have it re-check its reasoning, and to freeze decisions in a short status note first. A replier said they had not run a careful A/B.
  - Pattern across them (inference: findings/claude-code-model-switch-cache): people who switch per task split work across sessions or subagents instead of flipping one session; people who flip one session do it on judgment, and the ones who audited their logs found it costly. None of the threads measured a break-even for a switch.
  - Not covered: no thread read where the poster is on a Pro plan with usage limits as the concern rather than dollars; PullPush snapshot data may miss threads; seven threads are a small sample.
- **Evidence strength:** *official standard* (the tool vendor's own docs).
- **Sources:**
  - https://code.claude.com/docs/en/prompt-caching (official docs, read in full)
  - https://claude.com/blog/maximizing-the-value-of-your-claude-code-sessions (vendor blog, 2026-08-14)
  - https://support.claude.com/en/articles/14552983-models-usage-and-limits-in-claude-code (vendor help center; says nothing on cache cost of a switch)
  - https://platform.claude.com/docs/en/build-with-claude/prompt-caching (official API docs; pricing and invalidation sections read, the last part of the page was truncated and not read)
- **Limits:**
  - Neither page says how cached versus uncached tokens count toward Pro or Max usage limits, so how much a switch costs against a subscription's limit is *no data found*. The API price multipliers show the relative cost, not the subscription's accounting.
  - Switching back to the earlier model within its TTL probably reads the old cache (caches are per model and the old entry is separate), but no page says so. (inference: findings/claude-code-model-switch-cache)
  - A third-party guide says the same about Opus to Haiku; not relied on (unofficial).
  - Model names, multipliers and exceptions change with each release; hence the 6-month review.
- **Checked:** 2026-11-21
