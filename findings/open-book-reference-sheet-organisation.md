---
topic: open-book-reference-sheet-organisation
area: Career
question: For an exam or coding test that allows printed notes, does the way the sheet is organised (most-used content first, tiers, an index) matter, and which coding patterns are asked most often?
checked: 2026-11-26
review_months: 12
status: current
---
# Organising a printed reference sheet for a test, and which coding patterns come up most

- **Question:** For an exam or coding test that allows printed notes, does the way the sheet is organised (most-used content first, tiers, an index) matter, and which coding patterns are asked most often?
- **Finding:**
  - *Quality and organisation of the sheet go with better scores; having one does not by itself (research, small and correlational).* A Virginia Tech CS study found students did significantly better on comprehension questions when their crib sheet held good information on that topic. Engineering studies of student "support sheets" link sheet quality, organisation and density with better exam or course results. Dickson and Miller found authorised crib cards did not raise scores, and Ludorf and Clark found no significant link between the note features they measured and final exam scores, with weak inter-rater agreement on "organisation". Some studies find that allowing less content on the sheet raised scores, which they read as forced selection helping. Open-book tests raise scores on the first test but not long-term retention. Students report less anxiety with a sheet.
  - *No study found tests "most-used first" or tiered ordering of a sheet.* The research measures quality and organisation in general, not one ordering against another.
  - *Which coding patterns come up most (one vendor dataset).* PracHub tagged 2,818 company-named coding questions (a 2026-08-27 snapshot, 317 companies; one rule-based tag per question from the title and opening): stateful implementation and simulation 24.2%, strings and parsing 14.4%, trees and graphs 13.8%, arrays and hashing 13.1%, intervals and sorting 5.9%, stacks, queues, heaps, DP and similar 9.6%, unclassified 18.9%. Practitioner blogs rank hash maps and two pointers first, by opinion rather than data.
  - *Checker's inference (not in the sources):* when the test is close, re-ordering a long sheet buys little and risks errors. What helps is a one-page index at the front that maps a problem's cue words to a section and page number, tabs or margin numbers, and a single pass through the sheet with the pattern cues beside it, so the content can be found under time pressure. Put the most-asked types (stateful classes, strings, arrays and hashing, trees and graphs) where they are fastest to reach.
- **Evidence strength:** *anecdotal to weak research* for sheet organisation (small single-course correlational studies that disagree); *vendor data* for pattern frequency (one dataset with stated biases); the ordering advice is inference.
- **Sources:**
  - Virginia Tech study of crib sheets in a CS course (Shaffer, 2016): https://people.cs.vt.edu/shaffer/Papers/Crib_Sheets2016.pdf
  - Content analysis of student support sheets (ASEE): https://peer.asee.org/do-support-sheets-actually-support-students-a-content-analysis-of-student-support-sheets-for-exams.pdf
  - ERIC papers on crib sheets and open-book tests: https://files.eric.ed.gov/fulltext/EJ1223940.pdf, https://files.eric.ed.gov/fulltext/EJ1313187.pdf
  - PracHub analysis of coding-question patterns (fetched 2026-11-26): https://prachub.com/resources/most-common-coding-interview-patterns-by-company-analysis-of-prachub-question-data
  - Practitioner pattern lists (opinion): https://dglearning.substack.com/p/the-12-coding-patterns-that-cover, https://www.educative.io/blog/coding-interview-leetcode-patterns
- **Limits:** The sheet studies are summarised from search results; only the PracHub page was read in full. PracHub's own stated limits: it is not a random survey, one report can give several records, memorable questions may be overrepresented, and DP is undercounted. Its shares describe that dataset, not the chance of a pattern in any one test.
