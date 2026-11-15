---
topic: knowledge-register-maintenance
area: Software process
question: What keeps a register that gains entries constantly usable: owners, review dates, archiving, a generated index?
checked: 2026-11-15
review_months: 12
status: current
---
# Keeping a growing practice register maintainable

- **Question:** What do knowledge-base and decision-log practices say about keeping a register that gains entries constantly usable: ownership, review dates, archiving, and the index?
- **Finding:**
  - Knowledge-base guides agree that decay starts after publication. Each article gets an owner and a review date; at that date the owner updates it or archives it, then sets the next date.
  - Review cadence is set by how fast the content changes and what a stale answer costs, not one interval for everything. One source argues for change-triggered review over fixed dates; others keep fixed dates. Not every article needs an expiry date.
  - Archive, do not delete. Auto-archiving on date alone can remove content people still use, so an archive action carries a recorded reason, and the last-modified metadata is the currency signal (not dates written in the text).
  - The Thoughtworks Technology Radar shows an age-out model: an entry appears for one edition unless it changes status, older entries stay in an archive marked "not on the current edition" with a warning that the assessment may differ today. So "current", "aged out" and "superseded" are separate states; leaving the current view is not a verdict.
  - Docs guidance (Diátaxis and similar) groups by what the reader needs to do and audits pages against that; it is a way to organise the view, not a rule for folder counts. See [knowledge-register-layout](knowledge-register-layout.md) for flat files plus grouped index.
  - *Checker's inference for this register:* (1) the 12-month recheck rule creates one cliff, because most entries were written within a few weeks and all go stale together; a per-type interval (hiring-market and tool-behaviour entries short, method and process entries long) spreads it. (2) The index repeats each entry's Question line, so a fact lives in two places; generating the index from entry front matter (topic, area, checked, review interval) removes the copy and the manual sorting. (3) Splitting a topic that grows past a few paragraphs, and merging near-duplicates, is the same maintenance as archiving; none of the sources gives a size limit.
- **Evidence strength:** common practice for owner, review date and archive-not-delete (several independent vendor and university KB guides agree); vendor or single source for the Radar age-out detail; no data found for index generation from front matter or for a per-entry-type interval.
- **Sources:**
  - Knowmax, knowledge lifecycle management (vendor blog): https://knowmax.ai/feeds/blog/knowledge-lifecycle-management
  - Miami University, retire obsolete knowledge articles to archive (university IT best practice): https://miamioh.teamdynamix.com/TDClient/1813/Portal/KB/ArticleDet?ID=31049
  - University of the Fraser Valley IT service desk, review-date handling (university IT knowledge base): https://itservicedesk.ufv.ca/TDClient/52/ITServicesPortal/KB/ArticleDet?ID=8820
  - Supportbench, KB governance cadence (vendor blog): https://www.supportbench.com/?p=25227
  - ONES, knowledge collection (vendor blog): https://ones.com/blog/?p=1331170
  - Genesys community forum, stale-article policies (forum post, low authority): https://forum.sggu.com/t/architecting-content-lifecycle-management-policies-for-stale-knowledge-article-detection/1264
  - Thoughtworks Technology Radar FAQ (vendor docs): https://www.thoughtworks.com/en-de/radar/faq
  - Steve Arrants, documentation frameworks field guide (blog, low authority): https://stevearrants.substack.com/p/documentation-frameworks-a-field
- **Limits:** the sources are mostly customer-support knowledge bases and vendor blogs, a different setting from a register that agents read before searching; none measures a register of about a hundred entries. No source confirmed a standard `review_by` front-matter field. Read through search summaries, not full pages.
- **Checked:** 2026-11-15
