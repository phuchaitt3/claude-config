# Layout of a practice or decision register as it grows

- **Question:** Should a register of checked practices stay one flat folder as it grows, or move to categories or subfolders, and what keeps lookup working?
- **Finding:**
  - The Thoughtworks Technology Radar keeps one set of entries ("blips") and gives each a category (one of four quadrants) and a status (ring). Its FAQ says the quadrant "is not important", unlike the ring: the category is a label used to split the view, not a place an entry lives. Entries that stop moving leave the radar.
  - MADR's decision on categories ("Support Categories") picked subfolders with local IDs. It names the cost itself: an entry is hard to find when the reader does not know its category, and IDs are no longer unique.
  - log4brains keeps one global decision log plus per-package logs in a monorepo, all in one central repository.
  - Practitioner guides (low authority) call a flat docs folder of 20 or more files with no grouping a common problem, and suggest grouping by the reader's task, with directory READMEs and front-matter tags. Others report diminishing returns from heavy tagging.
  - *Checker's inference:* the sources agree on grouping the *view* (index sections, quadrants, tags) and split on moving *files* into folders. Where entry paths are cited from elsewhere, a category label in the index gives the grouping without breaking citations.
- **Sources:**
  - Thoughtworks Technology Radar FAQ (official, vendor): https://www.thoughtworks.com/en-de/radar/faq
  - MADR ADR-0010 "Support Categories" (project decision record): https://ruzickap.github.io/myteam-adr/madr/docs/0010-support-categories.html
  - log4brains README (tool docs): https://github.com/thomvaill/log4brains
  - adr-tools README (tool docs): https://github.com/strong-roots-capital/adr-tools
  - "Structure a knowledge base" (practitioner guide, low authority): https://tslateman.github.io/docs/how-to/structure-knowledge-base
  - Documentation organization ADR, a Python boilerplate project (single project, low authority): https://jojo275.github.io/simple-python-boilerplate/adr/034-documentation-organization-strategy
- **Limits:** no study compares flat, folder and tag layouts. The 20-file figure comes from practitioner write-ups, not measurement. The radar is a published snapshot, not a lookup register, so it is only an analogy. Read through search summaries.
- **Checked:** 2026-11-08
