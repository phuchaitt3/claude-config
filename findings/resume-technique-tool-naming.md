---
topic: resume-technique-tool-naming
area: Career
question: When a bullet names a method and the tool behind it, which form: "bge-m3 vector search", "vector search (bge-m3)" or "with bge-m3"?
checked: 2026-11-15
review_months: 12
status: current
---
# Naming a technique and the tool behind it in resume bullets

- **Question:** When a bullet names a method together with the model, library or service that implements it, which form is best: the tool as a modifier ("bge-m3 vector search", "PostgreSQL queue"), the technique with the tool in parentheses ("vector search (bge-m3)"), or "technique with/via tool"?
- **Finding:**
  - Guides agree on the content, not the punctuation: a bullet should carry both the skill a posting names and the specific tool, in the context of what was done with it, because recruiter searches and ATS match literal terms and generic categories alone ("dashboards", "a ticketing system") do not match a named tool. Typical formula: action verb, deliverable, tool, scale, outcome.
  - No source checked prefers one form over another, or says parentheses help or hurt parsing.
  - *Checker's inference:* "technique (tool)" is a good default when picked for consistency: the generic term a posting and a non-specialist reader recognise comes first, and an opaque name (a model id) follows as a qualifier. Exceptions where the form adds nothing: a tool that is the verb's object ("Integrated Socket.io"), a model that is acted on ("Fine-tuned Qwen2.5-0.5B-Instruct with LoRA"), and a phrase whose parentheses already hold an acronym ("explainable AI (XAI) with LIME"), to avoid stacked parentheses. Skills rows and stack lines stay plain lists. Pick one form and apply it across the whole resume (consistency is the one point the capitalization sources also stress: [resume-technical-term-capitalization](resume-technical-term-capitalization.md)).
- **Evidence strength:** vendor and career-site guides for the content point; no source for the form.
- **Sources:**
  - Jobscan, machine learning resume examples (vendor): https://www.jobscan.co/resume-examples/computer-engineering/machine-learning-resume
  - ResumeGeni, AI engineer resume guide (vendor guide): https://resumegeni.com/blog/ai-engineer-resume-examples
  - University at Buffalo Career Design Studio, ML engineer resume guide (university career centre): https://careerdesignstudio.buffalo.edu/blog/2025/10/28/ml-engineer-resume-guide-and-templates/
  - Careerflow, how to add hard skills to a resume (vendor blog): https://www.careerflow.ai/blog/how-to-add-hard-skills-to-resume
  - Enhancv, resume skills section (vendor blog): https://enhancv.com/blog/resume-skills-section/
- **Limits:** Read through search summaries; all sources are commercial or career-centre guides; none tests reader or ATS response to the form. The form chosen is a consistency choice, not a measured best.
- **Checked:** 2026-11-15

## Merged from `rag-reranking-spelling` (2026-11-24): "Reranking" or "re-ranking"

*Original question: Is "reranking" or "re-ranking" the more standard spelling in RAG and retrieval writing?* Cite this section as `findings/rag-reranking-spelling` (the old tag) or `findings/resume-technique-tool-naming`.

- **Question:** Which spelling is standard, for a resume that must match postings literally?
- **Finding:** Both are in use. Recent RAG guides (ZenML, Arize, Splunk, Vectorize, Sanity glossary) write "reranking"; the hyphenated form is the older research style (Nogueira and Cho, "Passage Re-ranking with BERT", 2019) and appears in some vendor text. Sanity's glossary lists "reranking" and "re-ranking" as the same stage. No source names one as the standard. *Checker's inference:* "reranking" is the more common modern spelling; the hyphen is not an error.
- **Evidence strength:** *vendor or single source* (blog and glossary pages seen in one search; no usage count; Sentence Transformers, Cohere and Pinecone docs not read).
- **Sources:** https://www.sanity.io/glossary/reranking , https://docs.zenml.io/user-guides/llmops-guide/reranking/understanding-reranking , https://arize.com/?p=33433 , https://www.splunk.com/en_us/blog/artificial-intelligence/reranker-models.html
- **Limits:** One standard search, no corpus count. Postings spell it either way (MoMo uses "re-ranking").
- **Checked:** 2026-11-19

## Merged from `resume-technical-term-capitalization` (2026-11-24): Capitalizing technical terms in resume bullets

*Original question: Should generic method names in resume bullets and skills rows be capitalized or lowercase?* Cite this section as `findings/resume-technical-term-capitalization` (the old tag) or `findings/resume-technique-tool-naming`.

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

## Merged from `resume-project-stack-line` (2026-11-24): Resume project stack line length

*Original question: How many technologies should a project's stack line list; is "at most 4–5" a rule?* Cite this section as `findings/resume-project-stack-line` (the old tag) or `findings/resume-technique-tool-naming`.

- **Question:** How many technologies should a project's stack line on a resume list, and is "at most 4–5" a real rule?
- **Finding:**
  - No source sets a firm limit. Guides converge on a short line of the **core** tools (language, framework, data store, platform), roughly 3–6 items; one guide's example line has five ("React, FastAPI, PostgreSQL, Docker, AWS"). They warn against listing obscure libraries, which clutters the line.
  - The common format is the stack on or just under the project heading, then 1–2 (up to 4) outcome bullets, plus a repository link. Recruiters say they screen for a relevant stack before reading bullets, so the line should be tailored to the posting.
  - ATS matching is on exact names (framework, tool), so a tool that matters to the posting should appear by its name somewhere: the stack line, a bullet or the skills section.
  - *Checker's inference:* "4–5 maximum" is a reasonable house limit inside the 3–6 range, not an industry rule. A master resume that is never sent can keep a longer line as the full record, as long as each sent version trims it to the tools the posting cares about and the bullets mention.
- **Sources:**
  - Instahyre, how to list projects on a resume (career site): https://resources.instahyre.com/blog/how-to-list-projects-on-resume/
  - Resumly, highlighting a tech stack without overwhelming recruiters or ATS (vendor blog): https://resumly.ai/blog/tips-for-highlighting-technical-stack-proficiency-without-overwhelming-recruiters-or-ats
  - DEV Community, "your junior developer resume is not a Pokémon collection" (community post): https://dev.to/guilherme_galanti/your-junior-developer-resume-is-not-a-pokemon-collection-1mm1
  - Onboarded, what a tech recruiter wants to see (recruiter newsletter): https://onboardedhq.substack.com/p/what-a-tech-recruiter-actually-wants-to-see-on-your-resume
  - ResumeGeni, entry-level software engineer resume (vendor guide): https://resumegeni.com/blog/entry-level-software-engineer-resume-guide
- **Limits:** All sources are career sites, vendor blogs or community posts; no study measured stack-line length. Numbers like "5–7" in some guides refer to a whole skills list, not one project. Read through search summaries; not every page was read in full.
- **Checked:** 2026-11-10

## Merged from `resume-skills-row-labels` (2026-11-24): Skills-row category labels for AI and ML engineer resumes

*Original question: What should the category labels of a skills section be for an AI/ML engineer resume (serving and infrastructure, retrieval and RAG), and may a row mix techniques with tools?* Cite this section as `findings/resume-skills-row-labels` (the old tag) or `findings/resume-technique-tool-naming`.

- **Question:** Which labels do guides use for skills rows that hold serving and deployment tools or retrieval and RAG items, and is a technique (cross-encoder reranking) acceptable beside named tools?
- **Finding:**
  - Guides agree skills are grouped by category with plain, standard headers so an ATS parses them; they do not agree on exact names. Labels seen: Languages, ML Frameworks, Cloud/MLOps, Databases, Specializations; "frameworks, infrastructure, serving and deployment, data processing, cloud ML services"; GenAI (LLMs, RAG, vector databases, prompt engineering); Infrastructure (Docker, Kubernetes, Terraform). `(inference: findings/resume-skills-row-labels)`
  - "Serving" alone is not used as a row label in the sources; "serving and deployment", "deployment" and "infrastructure" are. A label that pairs "Deployment" with "Infrastructure" matches the common wording.
  - For retrieval, the sources use "RAG" or "RAG & LLM Applications" as the umbrella and "Retrieval & Reranking" for the search items. A label with a search word plus "(RAG)" in parentheses was not found.
  - Techniques beside tools: a row may list techniques (hybrid search, cross-encoder reranking) with the tools that implement them; one guide lists reranking as a retrieval skill. Postings name the technique, so ATS matching favours keeping it (see [ats-keyword-matching](ats-keyword-matching.md)). No source says a row must hold only products.
  - Docker and Docker Compose are different things: Docker is the container platform, Docker Compose the tool that runs a multi-container app from one file. "Docker Compose" is the tool's own name, not a long form of "Docker"; guides list "Docker" in skills rows. The string "Docker Compose" still contains "Docker" for keyword matching. `(inference: findings/resume-skills-row-labels)`
- **Evidence strength:** vendor and career-site guides; none cites recruiter data on label wording. The labels chosen are a judgment call, not a measured best.
- **Sources:**
  - ResumeGeni, AI engineer resume guide (vendor guide): https://resumegeni.com/resume-guides/ai-engineer
  - ResumeGeni, AI engineer ATS keywords (vendor): https://resumegeni.com/blog/ai-engineer-ats-keywords
  - Scale.jobs, ML engineer resume guide (vendor): https://scale.jobs/resume-templates/machine-learning-engineer
  - Jobscan, machine learning resume examples (vendor): https://www.jobscan.co/resume-examples/computer-engineering/machine-learning-resume
  - Upgrad, RAG engineer job description (education vendor): https://www.upgrad.com/blog/rag-engineer-job-description
- **Limits:** Read through search summaries, not every page in full; all commercial. Related: [resume-skills-section-tailoring](resume-skills-section-tailoring.md).
- **Checked:** 2026-11-19
