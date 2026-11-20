---
topic: claude-pro-usage-limits
area: Agent setup
question: What are the 5-hour and weekly usage limits on the $20 Claude Pro plan, are token figures published, and can a user work out the size of the weekly limit?
checked: 2026-11-20
review_months: 6
status: current
---
# Claude Pro (the $20 plan) usage limits: structure, published numbers, and measuring the weekly cap

- **Question:** What limits does the $20 Claude Pro plan have for Claude Code, does Anthropic publish their size in tokens, and can the weekly limit be measured from the machine's own data?

- **Finding:**
  - **Structure (official help pages):** two limits apply, a session limit that resets every five hours and a weekly limit across all models that resets once a week at a fixed time assigned to the account. Claude chat, Claude Code and the desktop app draw from the same pool. The next reset time is shown in Settings > Usage (and `/usage` in Claude Code). Hitting either limit stops use.
  - **Size: not published.** No official page read gives a token count or hour count for the weekly limit; a GitHub documentation issue (#11418) asks for exactly this. Third-party figures (for example "40 to 80 hours of Sonnet a week", "200k tokens per 5 hours") are older, unofficial and differ between sources; do not use them.
  - **Promotions change the numbers.** A search summary of the help centre reports a 50% higher weekly Claude Code limit from 13 May to 31 August 2026 (not read on the page; if true it has ended). Peak-hour effects on the 5-hour limit are reported by secondary sources and one says they were removed; unverified. Re-measure after any announced change.
  - **What a program can read (official, see `findings/claude-code-usage-limit-resume`):** the status line receives `rate_limits.five_hour` and `rate_limits.seven_day` as `used_percentage` plus `resets_at`. The percentages are whole numbers.
  - **Measuring the weekly cap (checker's own method, one data point):** log the weekly percentage over time and divide the tokens all local chats used in the same interval by the rise in percent. First window, 2026-11-19 to 11-20: weekly 61% to 75% (14 points) over 16.8 hours, with 15.7M weighted tokens in the local transcripts (input x1, cache write x1.25, cache read x0.1, output x5; the weights are the API price ratios, not a published meter), giving about 1.1M weighted tokens per point, about 112M for the full week. One window with a rise of 14 whole points carries a rounding error of about 7%, plus unknown use from other devices and claude.ai (which makes the cap look smaller than it is) and an unmeasured model mix (Opus use is weighted like Sonnet). Treat it as an order of magnitude until several windows agree.
  - **Why the percentage log alone is not enough for one run:** the percentage is whole-account, so it also counts every other chat in the run's window. Dividing a run's own tokens by a measured tokens-per-point constant attributes the run exactly and needs the percentage only for calibration.

- **Evidence strength:** *official standard* for the two-limit structure, the shared pool and the status line fields (help pages, hooks and status line docs); *vendor or single source* and secondary for promotions and peak hours; *sample of one window* for the measured cap (checker's own, local).

- **Sources:**
  - About Claude's Pro plan usage (official help page): https://support.claude.com/en/articles/8324991-about-claude-s-pro-plan-usage
  - Usage and length limits (official help page): https://support.claude.com/en/articles/11647753-usage-and-length-limits
  - Weekly limit documentation gap (GitHub issue, anthropics/claude-code #11418): https://github.com/anthropics/claude-code/issues/11418
  - Weekly caps announced July 2025 (trade press): https://techcrunch.com/2025/07/28/anthropic-unveils-new-rate-limits-to-curb-claude-code-power-users/
  - Claude Code limits, 5-hour and weekly windows (secondary guides, disagree on details): https://portkey.ai/blog/claude-code-limits ; https://www.datacamp.com/tutorial/claude-code-usage-limits
  - Status line `rate_limits` fields (official docs): https://code.claude.com/docs/en/statusline

- **Limits:** The help pages were seen only as search snippets in this check, not read in full; the promotion dates come from a search summary. No source gives the weekly size; the measured cap is one window. Whether the meter counts cache reads at 0.1 is not published. Weekly reset timing is account-specific.

- **Checked:** 2026-11-20
