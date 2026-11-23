---
topic: knowledge-register-entry-granularity
area: Software process
question: How do knowledge bases and note systems stop one-fact entries piling up: search before creating, append to the existing entry, or a size floor?
checked: 2026-11-23
review_months: 24
status: current
---
# Keeping entries from fragmenting when they are added one at a time

- **Question:** How do knowledge bases and note systems keep entries from fragmenting into one fact each, when entries are added one at a time and a periodic regrouping of old entries is not wanted?
- **Finding:**
  - Knowledge-base tools prevent duplicates at creation time: ServiceNow's documented duplicate-detection setting shows similar existing articles to the author as they create a new one, so they can update an existing article instead. Document360 names the cause as teams creating new articles instead of updating existing ones.
  - When duplicates already exist, UCLA's knowledge-base guidance is to combine them into one and leave the other as a pointer, so existing links keep working. This matches this register's "old tags keep resolving" rule.
  - Note systems agree on updating the existing note when a concept recurs (Fabric's evergreen-notes guide), and on one concept per note (Matuschak). A few hundred words in one note is a sign it covers more than one concept. A Zettelkasten forum thread argues atomicity is often reached by splitting a note later, not by writing small notes first.
  - So the sources support a write-time nearest-entry check plus "append when the concept recurs"; they do not give a number for how narrow an entry may be.
  - *Checker's inference (not sourced):* (1) a nearest-entry list built from word overlap fits clusters of related entries but cannot help an entry with no neighbour; a prototype on 12 known one-fact entries found neighbours (score 0.26 to 0.39) for 7 and nothing above 0.10 for 4; the 12th was missed by the prototype's own same-area filter. (2) For those, the only lever is a floor on what an entry must contain (for example two sourced lines, or a decision no other entry covers). (3) A "state in one line why this is separate" step is a reasoned guess, not a documented practice.
- **Evidence strength:** *common practice* for search-before-create and update-instead-of-duplicate (ServiceNow docs, BMC and university KB guidance agree); *vendor or single source* for the note-system points; *no data found* for a size floor, or for a nearest-entry check applied by an automated agent.
- **Sources:**
  - ServiceNow, identify and resolve duplicate articles (vendor docs): https://www.servicenow.com/docs/r/Ir~NPf1dr8MGFXQE6QlBoQ/SP33hraAhYyw_rYTXb1Llg
  - ServiceNow community thread on avoiding duplicate knowledge creation (forum, low authority): https://www.servicenow.com/community/servicenow-otto-forum/avoiding-duplicate-knowledge-creation/m-p/3176569
  - UCLA knowledge base, what to do about duplicate articles (university IT guidance): https://bookstack.kb.ucla.edu/books/about-this-knowledge-base/page/what-to-do-about-duplicate-knowledgebase-articles
  - Document360, fix duplicate content in a knowledge base (vendor blog): https://document360.com/blog/fix-duplicate-content-in-knowledge-base/
  - Matuschak, evergreen notes should be atomic (author's working notes): https://notes.andymatuschak.org/Evergreen_notes_should_be_atomic
  - Fabric, evergreen notes (vendor guide): https://fabric.so/learn/evergreen-notes
  - Zettelkasten forum, principle of atomicity (community post): https://zettelkasten.de/posts/principle-of-atomicity-difference-between-principle-and-implementation/
- **Limits:** the sources are customer-support knowledge bases and personal note-taking; neither is a register that agents write to and read before searching. Wikipedia's duplicate-article policy was searched for and not found. Read through search summaries, not full pages. The proposal this supports (a write-time nearest-entry check plus a scope floor) is not yet adopted.
- **Checked:** 2026-11-23
