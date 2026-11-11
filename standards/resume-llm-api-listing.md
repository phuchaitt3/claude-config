# Listing LLM APIs (OpenAI, DeepSeek, ...) on a resume

- **Question:** Is naming a hosted LLM API (OpenAI API, DeepSeek, Anthropic, Gemini) on a resume worth anything, or does it read as low-effort "wrapper" work? And when several APIs were used, which should be named?
- **Finding:**
  - Naming the API is fine as a keyword: AI-engineer guides list "LLM APIs (OpenAI, Anthropic, Gemini)" in the skills section and say to mirror the posting's wording; ATS matching rewards the exact name. No source says the name itself hurts.
  - The name earns nothing on its own. "Built a wrapper over the OpenAI API" is called generic by recruiters' guides; what counts is what was built around the call: retrieval and chunking choices, an evaluation set and metric, LLM-as-a-judge evaluation, structured output or tool calls, cost control (caching, routing), failure handling. Put the API inside a bullet about that work rather than as a headline.
  - Consumer use (ChatGPT) does not belong on a technical resume.
  - Model-centred roles (ML engineer, research) weigh model work over API integration; the API keyword fits application-focused (AI engineer) roles better.
  - *Checker's inference:* name an API where it is part of the system that was built (the generator in an app: stack line plus a bullet). An API used only as an evaluation judge is better shown as the method ("LLM-as-a-judge via Ragas") with the judge model named in the bullet or kept for the interview; listing it as a separate skill adds a provider name, not a skill. A skills row may group them ("LLM APIs: OpenAI, DeepSeek") for application-focused postings and drop the row for model-focused ones.
- **Sources:**
  - Careery, AI engineer resume guide (career site): https://careery.pro/blog/ai-careers/ai-engineer-resume-guide
  - Jobrise, mentioning AI skills without sounding fake (career site): https://jobrise.io/en/blog/how-to-mention-ai-skills-on-resume/
  - ResumeGeni, AI engineer resume guide (vendor guide): https://resumegeni.com/blog/ai-engineer-resume-guide
  - FACE Prep, framing ChatGPT-wrapper projects on a resume (education blog): https://faceprep.in/article/how-to-frame-chatgpt-wrapper-projects-on-resume-2026/
  - techinterview.org, what "built with AI" means in 2026 interviews (community post): https://www.techinterview.org/post/3233475399/ai-portfolio-built-with-ai-2026-interviews/
  - My Engineering Path, GenAI engineer portfolio guide (personal site): https://myengineeringpath.dev/genai-engineer/portfolio-guide/
- **Limits:** SEO-oriented career and vendor content from 2025–2026, no hiring-manager study; statistics quoted in them (e.g. "80% skip testing") are unsourced. Read through search summaries.
- **Checked:** 2026-11-11
