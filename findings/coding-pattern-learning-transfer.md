---
topic: coding-pattern-learning-transfer
area: Career
question: When learning coding-interview patterns, is one worked problem per pattern enough, or does it lead to memorising that problem? How many problems, in what order, and how is recognition trained?
checked: 2026-11-22
review_months: 12
status: current
---
# Learning a coding pattern so it transfers, not one memorised problem

- **Question:** When learning coding-interview (LeetCode-style) patterns, is one worked problem per pattern enough, or does it lead to memorising that problem? How many problems, in what order, and how is recognition trained?
- **Finding:**
  - *One example rarely transfers; comparing two does (research, other fields).* Gick and Holyoak (1983, *Cognitive Psychology*) found that people given two analogous stories often formed a general problem schema as a by-product of saying how they were alike, and then transferred it; summaries and later papers note that people given one source story often fail to use it on a remote problem. Statements and diagrams of the principle that did not help with one analogue helped when paired with two. Gentner, Loewenstein, Thompson and Forbus (2009) report that comparing two examples makes their shared structure stand out, while cases studied one at a time are encoded in a context-specific way. Catrambone and Holyoak (1989) found the quality of the schema formed predicted transfer.
  - *Mixed practice trains choosing the method (research, mathematics).* Rohrer, Dedrick and Stershic (2015, classroom study) found interleaved homework beat blocked homework on an immediate and a delayed test (Cohen's d about 0.42 and 0.79). The stated reason: blocked practice lets a student finish without knowing which kind of problem it was, while mixed practice makes them pick the strategy from the problem itself, as a real test does. Rohrer, Dedrick and Burgess (2014) found the benefit held for problem types that look quite different, so it is not only about telling look-alikes apart. How much blocked practice should come first for new material is an open question in the secondary sources.
  - *Coding prep blogs converge on a few problems per pattern, then spaced re-attempts.* Guides suggest about 3 to 7 problems per pattern (one guide: 3 to 5 canonical ones studied slowly with narration, then 10 to 15 more from lists such as NeetCode 150 or Grind 75), re-attempted from the problem statement on a spaced schedule rather than re-reading solutions. One blog keeps only the problem statement in its review deck. The numbers are heuristics; none of these sources measured them.
  - *Checker's inference (not in the sources):* for a short timeline, a pattern is taught through at least two problems that look different on the surface, with the shared Shape written out after both; later problems come unlabelled and mixed with earlier patterns so the learner has to pick the pattern; a pattern counts as learned when a new, unlabelled problem is solved cold on a later day. This agrees with `findings/effective-study-techniques` (worked example first for novices, then practice; mixing beats blocking; spaced retrieval) and `findings/coding-problem-pattern-vs-basics-order`.
- **Evidence strength:** *common practice* for the general learning effects (analogical comparison and interleaving each have several studies that agree); *anecdotal* for coding-specific numbers (blogs and vendor pages).
- **Sources:**
  - Gick and Holyoak 1983, schema induction and analogical transfer (university repository): https://deepblue.lib.umich.edu/items/196ea13e-fb69-4a74-a6f9-864c81aed465
  - Gentner, Loewenstein, Thompson and Forbus 2009, reviving inert knowledge by comparison (university paper): https://www.qrg.northwestern.edu/papers/Files/QRG_Dist_Files/QRG_2009/Gentner,Loewenstein,Thompson&Forbus_2009-1.pdf
  - Catrambone and Holyoak 1989, overcoming contextual limits on transfer (university paper): https://sites.lifesci.ucla.edu/psych-reasoninglab/wp-content/uploads/sites/273/2021/04/Catrambone_Holyoak1989.pdf
  - Rohrer, Dedrick and Burgess 2014, interleaving with dissimilar problem types (journal article): https://link.springer.com/article/10.3758/s13423-014-0588-3
  - Rohrer and Hartwig, spaced and interleaved mathematics practice (university handout): https://www.unh.edu/teaching-learning-resource-hub/sites/default/files/media/2023-06/itow-spaced-and-interleaved-mathematics-practice-rohrer-hartwig.pdf
  - Recognising LeetCode patterns without memorising solutions (blog): https://dev.to/alex_hunter_44f4c9ed6671e/how-to-recognize-leetcode-problem-patterns-without-memorizing-every-solution-2ed7
  - Learning patterns by practising less (blog): https://medium.com/@codegrey/the-science-behind-learning-patterns-how-i-learned-more-by-practicing-less-fbae32e32c2e
  - Spaced repetition for LeetCode (vendor blog): https://leetsrs.pages.dev/blog/spaced-repetition-for-leetcode
- **Limits:** Search summaries, not full papers, were read; the single-analogue condition figures in Gick and Holyoak were not checked. The research uses story problems, physics or school mathematics, not programming. The coding sources are blogs and vendors with no measured outcomes, and their problem counts disagree. Reddit was not searched.
- **Checked:** 2026-11-22
