---
topic: resume-skills-row-labels
area: Career
question: What should the category labels of a skills section be for an AI/ML engineer resume (serving and infrastructure, retrieval and RAG), and may a row mix techniques with tools?
checked: 2026-11-19
review_months: 12
status: current
---
# Skills-row category labels for AI and ML engineer resumes

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
