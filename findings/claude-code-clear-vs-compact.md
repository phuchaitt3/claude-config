# When to clear or compact a Claude Code chat

- **Question:** What is recommended about when to `/clear` or `/compact` a Claude Code chat?
- **Finding:**
  - Anthropic's best-practices page (official docs): compaction happens automatically before the window fills, and with a 1M-token window on most current models running out of context is rare. The reason to manage context is cost and focus: every request re-sends the whole conversation, so a session holding three unrelated tasks re-reads all three on every turn of the fourth (cheaper while the prompt cache is warm, full price after it expires).
  - `/clear` between unrelated tasks: it costs nothing and the next task stops paying for the old history. `/clear <name>` names the session left so it can be resumed later.
  - `/clear` after two failed corrections of the same mistake: a third correction only adds to a conversation that already holds two failed attempts; `/clear` plus one new prompt that folds in what was learned "works better almost every time".
  - `/compact` with a focus (for example "keep the API changes and the test commands") when the task continues. On a long session `/compact` is itself a big request, since it reads the whole conversation, more so once the cache has expired. The docs say a session past about 200K tokens that sits idle is compacted shortly before the one-hour cache expires; if the history is not needed, a fresh session costs less.
  - The docs mark the older advice "manage the window aggressively" as outdated: `/clear` between tasks is still worth doing, but subagents and constant compaction to avoid running out are no longer the main reason.
  - Third-party guides (blogs, course pages) repeat the split and add thresholds such as compacting manually near 60% utilisation, and warn that `/compact` loses exact code from earlier. These thresholds are rules of thumb; no source measures them.
- **Evidence strength:** *official standard* for the `/clear` between tasks, `/clear` after two failed corrections and `/compact <focus>` points (Anthropic's own docs). *Anecdotal* for the 60% threshold and the lost-code warning (third-party guides, about 15 read in search snippets, none with data).
- **Sources:**
  - Anthropic, "Best practices for Claude Code" (official docs, section on context): https://code.claude.com/docs/en/best-practices
  - Third-party guides, for example https://dev.to/stacknotice/claude-code-compact-vs-clear-2026-managing-long-sessions-without-losing-quality-4dhm and https://buttondown.com/redpen/archive/clear-vs-compact-two-ways-to-fight-a-growing/ (community posts)
- **Limits:** The official page was read through a summarising fetch tool (the context passages were located by search of the saved text). The cache and size figures are the docs' own and may change with the model or plan. Third-party thresholds were only seen in search summaries. Existing rule `workflow-rules "Context"` (clear at task boundaries, compact only when the task continues) matches the docs; the "about 15 tool calls" and "40 tool calls" triggers are the user's own and not from a source.
- **Checked:** 2026-11-13
