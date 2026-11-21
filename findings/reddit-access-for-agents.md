---
topic: reddit-access-for-agents
area: Agent setup
question: Can an agent read Reddit threads or find Reddit post URLs in 2026, and which routes exist (search tools, public JSON, official API, archives, paid scrapers)?
checked: 2026-11-21
review_months: 6
status: current
---

# Reddit access for an agent

- **Question:** Can an agent read Reddit posts, and can it get the post URLs?
- **Finding:**
  - Tested in this repository (2026-11-19 and 2026-11-21): the web search tool never returned a Reddit thread (five queries, including `site:`-style and `reddit.com/r/.../comments` forms); `WebFetch` refuses the domain; a plain request gets 403; DuckDuckGo's HTML page answers a script with a bot challenge (HTTP 202) and Bing's returned no Reddit links; two news sites that cite Reddit threads also answered 403 to both the fetch tool and the user's `webx`. So there is no tool in this setup that lists Reddit URLs for a query.
  - Why, as vendor blogs report it (see Limits): Reddit stopped logged-out `.json` access in late May 2026 (appending `.json` now gives 403); RSS was announced to end 2026-11-13; new Data API applications need approval under the Responsible Builder Policy (introduced Nov 2025) and were reported closed 2026-10-31; remaining public API access was reported to end March 2027. The dates differ between sources.
  - Routes still reported to work: (1) the official OAuth API with credentials from an already approved app, non-commercial, about 100 queries per minute per client; it includes subreddit search, which returns post URLs; (2) historical archives (PullPush, Arctic Shift) for older posts; (3) paid scraping or data APIs, which are outside Reddit's terms or need a licence; (4) headless-browser scraping, reported as harder and against the terms.
  - Reddit's terms forbid scraping outside the API and model training on the data without Reddit's agreement (as one vendor blog summarises them).
  - (inference: findings/reddit-access-for-agents) With the user's `webx`, a thread URL can be read through the official API; a subreddit search through the same keys would return URLs, but a script of the agent's own that loads those keys was refused by the permission classifier on 2026-11-21. Until the user allows it or supplies URLs, the URL step stays a hand-off (`findings/README.md`, Reddit section).
- **Evidence strength:** *anecdotal* (vendor and developer blogs that sell Reddit data tools, conflicting on dates) for what Reddit changed; first-hand test in this repository for what the agent's tools can and cannot reach.
- **Sources:**
  - https://crawlora.net/blog/reddit-json-api-blocked-2026 (vendor blog, `.json` block)
  - https://scrapecreators.com/blog/reddit-rss-public-api-shutdown (vendor blog, RSS and API dates)
  - https://ppc.land/reddit-to-halt-public-data-api-access-in-march-2027-as-14-000-apps-register/ (trade press, March 2027)
  - https://www.redditapis.com/blogs/reddit-data-api-2026 (vendor blog, approval and Responsible Builder Policy)
  - https://data365.co/blog/reddit-api-limits (vendor blog, rate limit)
- **Limits:** Only search snippets of these pages were read, not the pages; none is Reddit's own announcement (r/redditdev, r/modnews and the Data API Terms were not readable and not checked). Sources disagree on the 10 versus 100 queries-per-minute limits and on the shutdown dates. Several sources sell Reddit scraping, so they have a reason to stress the block. Reddit policy is changing quickly, hence the 6-month review.
- **Checked:** 2026-11-21
