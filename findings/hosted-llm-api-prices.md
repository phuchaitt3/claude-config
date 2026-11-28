---
topic: hosted-llm-api-prices
area: ML systems
question: What do the cheapest hosted text, embedding and rerank APIs cost, and which have a free tier? (Separate entry: no other entry records API prices.)
checked: 2026-11-28
review_months: 6
status: current
---
# Hosted model API prices

- **Question:** What does a small hosted setup cost per million tokens?
- **Evidence strength:** vendors' own pricing pages, read on the date below. Prices change often: recheck before spending.
- **Finding (USD per million tokens, input / output):**
  - OpenAI `gpt-5-nano` 0.05 / 0.40; `gpt-6-luna` 0.10 / 0.50; no free API tier listed for text models.
  - Anthropic Claude Haiku 5.5, prompts up to 100k tokens: 0.10 / 0.50; only unspecified trial credits.
  - Google Gemini 3.5 Flash-Lite 0.30 / 2.50; a free tier exists, and free-tier data is used to improve Google's products (paid tier: not).
  - Cloudflare Workers AI: 10,000 neurons a day free, requests fail beyond it on the free plan; `bge-m3` 0.012 and `bge-reranker-base` 0.003 per million input tokens; `bge-reranker-v2-m3` is not listed.
- **Sources (official pricing pages):** https://developers.openai.com/api/docs/pricing , https://platform.claude.com/docs/en/about-claude/pricing , https://ai.google.dev/gemini-api/docs/pricing , https://developers.cloudflare.com/workers-ai/platform/pricing/
- **Limits:** not exhaustive (Groq and others publish prices elsewhere); no model's quality in any language was checked; hosting of the app and database is not included.
- **Checked:** 2026-11-28
