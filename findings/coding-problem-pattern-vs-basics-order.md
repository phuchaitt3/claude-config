---
topic: coding-problem-pattern-vs-basics-order
area: Career
question: For coding-interview (LeetCode-style) preparation, is it better to learn problem patterns first or the basics of each data structure first?
checked: 2026-11-20
review_months: 12
status: current
---
# Patterns first or data-structure basics first

- **Question:** For coding-interview (LeetCode-style) preparation, is it better to learn problem patterns first, or the basics of each data structure first?
- **Finding:**
  - *Guides mostly say a short basics pass, then patterns.* Educative's roadmap has a foundation phase (arrays, strings, hash maps, recursion, sorting, on easy problems), then a phase of recurring patterns (binary search, DFS/BFS, backtracking, dynamic programming, greedy) described as the templates strong engineers recognise quickly. A HackerNoon article says to order patterns by how often LeetCode reports them in interviews. One GitHub guide says to leave the hardest problems to last. All are prep-blog or vendor material, not studies.
  - *A patterns-first view exists* in LinkedIn posts ("master the patterns first", one pattern at a time, 2 to 4 problems each). Low authority; no evidence given.
  - *No study compares the two orders for coding interviews.* The search found none.
  - *Related research on recognising problem types (other fields).* In physics and statistics, novices sort problems by surface features (the words "incline", "pendulum") and experts by the underlying principle (Chi lineage; Hardiman, Dufresne and Mestre 1989, where experts used deep structure but surface similarity still hurt them). Novices who categorised by principle also scored higher at solving. No programming study was found.
  - *Checker's inference (not in the sources):* the recognition skill is real and worth training, but it is a skill built on the basics: a pattern's "Shape" is described in terms of the structure it uses (a hash map, a stack, a heap), so a learner who cannot use that structure cannot apply the pattern even after recognising it. A workable order for a short timeline is one small worked example of the structure, then the pattern's cue (shape, keywords, "fails when"), then a problem attempt, with new problems from mixed patterns on later days so the cue is chosen, not given. This agrees with the worked-example advice in `findings/effective-study-techniques` (novices: study an example first, then practise; mixing beats blocking).
- **Evidence strength:** *anecdotal* for the coding-specific order (blogs and posts that agree loosely); *common practice* only for "basics pass, then patterns". The expertise research is from other fields.
- **Sources:**
  - Educative, LeetCode roadmap (vendor blog): https://www.educative.io/blog/leetcode-roadmap
  - HackerNoon, 5 to 23 patterns to ace any coding interview (blog): https://hackernoon.com/5-to-23-patterns-to-ace-any-coding-interview
  - LeetCode study guide (GitHub): https://github.com/YouGoDevs/LeetcodeStudyGuide
  - Experts and novices, problem categorisation and problem solving (university publication page): https://experts.illinois.edu/en/publications/the-relation-between-problem-categorization-and-problem-solving-a/
  - Hardiman, Dufresne, Mestre, problem representation in experts and novices (journal article, abstract): https://core.ac.uk/works/13490922
  - Assessing expertise in introductory physics with a categorisation task (preprint): https://arxiv.org/pdf/1602.08781
- **Limits:** Search results and snippets only; the vendor blogs sell courses; the LinkedIn posts are unverified. The categorisation research is about physics and statistics, not programming, and describes sorting problems, not a teaching order. Nothing measured pass rates for either order.
- **Checked:** 2026-11-20
