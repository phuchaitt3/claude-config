# Capitalizing technical terms in resume bullets

- **Question:** In resume bullets and skills rows, should generic method names ("cross-encoder reranking", "hybrid search", "semantic chunking") be capitalized, or written in lowercase like ordinary nouns?
- **Finding:**
  - Style guides lowercase common nouns, technical terms included, and capitalize only proper nouns, product and model names (in their official form, e.g. "bge-m3", "PostgreSQL", "Qwen3-Reranker-0.6B") and acronyms. Google's developer style guide says to avoid unnecessary capitalization and to lowercase glossary terms unless they are proper nouns.
  - Resume guides apply the same rule: field names that are not proper nouns stay lowercase, acronyms stay uppercase, and whatever style is chosen is applied consistently.
  - *Checker's inference:* a named method that is a proper noun in the literature keeps its capitals only if its source writes it that way ("Reciprocal Rank Fusion" is commonly capitalized after its paper title; lowercase is also common). ATS keyword matching is usually case-insensitive, so lowercase costs no match; no source checked this directly.
- **Evidence strength:** official standard (Google style guide) for prose; vendor or single source for resumes.
- **Sources:**
  - Google developer documentation style guide, Capitalization (official style guide): https://developers.google.com/style/capitalization
  - Google developer documentation style guide, Product names (official style guide): https://developers.google.com/style/product-names
  - Resume Worded, how to correctly capitalize your resume (vendor blog): https://resumeworded.com/blog/resume-capitalization-post
- **Limits:** No source addresses ML method names on resumes specifically; the resume source is one vendor blog read through a search summary. Skills-section list items are covered only by the Google guide's sentence-case rule for list items.
- **Checked:** 2026-11-13
