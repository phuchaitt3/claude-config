---
topic: web-scraper-hidden-tab-content
area: Agent setup
question: Do specialised scraping tools (Firecrawl, Crawl4AI, Jina Reader, Apify crawlers) return tab and accordion content with each body under its heading, or does that need page interaction?
checked: 2026-11-20
review_months: 6
status: current
---

# Tab and accordion content in web-to-Markdown tools

- **Question:** do specialised scrapers return tabbed and accordion content in reading order (heading, then its body) on their own, or is a click step the normal answer?
- **Finding:**
  - Content behind a tab or accordion is usually already in the page's HTML at first load; it is hidden by styling, not absent. A search-marketing guide says to test this by searching the page source for the text. (sourced: Search Engine Journal)
  - The documented way the tools reach hidden or lazy content is to click first, then extract: Firecrawl "actions" (click, wait, scroll, type; up to 50 per request, run before extraction), Crawl4AI `js_code` with `wait_for` and `session_id`, Apify Website Content Crawler "Expand clickable elements". (sourced: vendor docs below)
  - Firecrawl's `onlyMainContent` defaults to true and drops headers and navigation, so content placed in such regions can be lost; set it false to check. (sourced: Firecrawl docs)
  - None of the sources found says a tool re-attaches an accordion panel to its heading automatically. (inference: findings/web-scraper-hidden-tab-content; no source says it does not either)
- **Own test, one page, 2026-11-20 (anecdotal):** a landing page built with a page-builder (tabs per capability stream, FAQ accordion, no `<img>` tags). Three extractors, none restored heading-to-body pairing:

  | Extractor | Size | Tab bodies | FAQ |
  |---|---|---|---|
  | trafilatura on the static HTML | 13.5k chars | present, detached from their headings | answers only, no questions |
  | Crawl4AI headless browser | 20.6k chars | headings only, bodies elsewhere | questions only, answers detached; plus a form-dropdown dump |
  | Jina Reader (`r.jina.ai`, free) | 6.7k chars | absent | questions only, no answers |

  The static extractor kept the most text. Firecrawl was not run (it needs the account's quota and key).
- **Evidence strength:** *common practice* for "click actions are the route" (several vendor docs agree); *anecdotal* for the test (one page, three tools, Firecrawl missing).
- **Sources:**
  - [Search Engine Journal: can AI systems render JavaScript to read hidden content](https://www.searchenginejournal.com/ask-an-seo-can-ai-systems-llms-render-javascript-to-read-hidden-content/563731) (trade press)
  - [Firecrawl: Introducing Actions](https://www.firecrawl.dev/changelog/actions) and [advanced scraping guide](https://docs.firecrawl.dev/advanced-scraping-guide) (vendor docs)
  - [Apify Website Content Crawler](https://apify.com/website-content-crawler) (vendor page)
  - Crawl4AI page-interaction and content-selection docs, read through Hugging Face mirrors of the repository, not the official site: [page-interaction.md](https://huggingface.co/spaces/theYEH/Crawl4AI/blob/main/docs/md_v2/basic/page-interaction.md) (mirror of vendor docs)
- **Limits:** Firecrawl's and Crawl4AI's behaviour on tabs was read from documentation, not run. The Crawl4AI sources are mirrors, so parameter names may be out of date. One page does not show how common the problem is. The search found no benchmark of heading-to-body fidelity across tools.
- **Checked:** 2026-11-20
