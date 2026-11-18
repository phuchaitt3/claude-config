---
topic: ai-engineer-skill-demand
area: Career
question: How common is each skill family (RAG, fine-tuning, agents and MCP, evaluation, hallucination detection, serving) in AI-engineer job postings, and is any of them "core" for the role?
checked: 2026-11-18
review_months: 6
status: current
---
# How common each AI-engineer skill is in job postings

- **Question:** For deciding which skills belong in an AI-engineering resume base: how often does each skill family appear in AI-engineer postings, and what counts as "generally required"?
- **Finding:**
  - **No source defines "core" or gives a share at which a skill counts as required.** The only labelled tiers found are one author's: above 50% "table stakes", 20-50% "common", 5-20% "differentiators" (DEV post below). Any threshold is a project's own choice. `(inference: findings/ai-engineer-skill-demand)`
  - **Counts conflict by a wide margin**, because samples, skill dictionaries and matching differ. Per family (share of AI-engineer postings):

    | Family | 3,449 postings, InterviewStack board, May 2026 | 903 postings, Glassdoor US, Apr 2026 | 390 postings, source unnamed (secondhand, KDnuggets Oct 2026) | Other |
    |---|---|---|---|---|
    | Python | 71% | 71% | | |
    | LLMs (as a keyword) | 66% | | | |
    | RAG | 40% | 13.6% | 26% | |
    | Fine-tuning (any) | not reported | 14.8% | | about 18% of LLM postings in one market breakdown (see `findings/lora-vs-qlora`) |
    | AI agents | not reported | 10.6% (multi-agent 3.4%) | 50% | about 16% of Hacker News job posts (agents), snippet only |
    | Evaluation | not reported | "model evaluation" 5.5% | 56% ("AI evaluation") | about 3.2% of Hacker News job posts ("evals"), snippet only |
    | MCP | not reported | not reported | not reported | about 2.7% of Hacker News job posts, snippet only; a tracker counts 23,521 postings naming it across 5,438 companies (all roles) |
    | Hallucination detection | not reported | not reported | not reported | no count found |
    | Serving (vLLM and similar) | not reported | no count | not reported | no aggregate; individual postings ask for it mainly in inference-focused roles, often as one of several accepted engines |
    | LoRA/QLoRA by name | not reported | not reported | not reported | no count; named with PEFT in 2026 LLM-engineer postings (see `findings/lora-vs-qlora`) |
    | Docker / Kubernetes | 18% / 16% | 15.4% / 17.6% | | |

  - **Reading across the table** `(inference: findings/ai-engineer-skill-demand)`: RAG is the only family counted by three independent samples, and it is mainstream in all of them (14% to 40%). Agents and evaluation range from about 5% to over 50%, so no direction can be read from the data; the 390-posting figures (50-56%) are the highest and the least traceable. Fine-tuning sits around 15-18%, a specialty rather than a baseline. MCP, hallucination detection and vLLM by name have no AI-engineer share; the only MCP figure is a small share of general tech posts.
  - **Vietnam, entry level (search snippets of ITviec, TopDev and company pages, no counts):** fresher and junior postings ask for Python, NLP, RAG (chunking, embeddings, retrieval, reranking), prompt work and LLM basics; LangChain, LangGraph and LlamaIndex recur; vector databases are usually nice-to-have; LoRA/QLoRA and PEFT are named mainly in middle and senior postings, with fresher postings asking for data preparation and an understanding of fine-tuning. A few postings name serving open-source models with vLLM or Ollama. Postings found were a handful, one dated Aug 2025. `(sample: about 10 postings seen, not counted)`
- **Evidence strength:** *sample or survey* for the counts (vendor and community analyses; two of three name their data source, one is secondhand with no named source); *anecdotal* for the Vietnam postings; *no data found* for hallucination detection, MCP among AI-engineer postings, and vLLM by name.
- **Sources:**
  - [AI Engineer skills companies want in 2026: 3,449-posting analysis](https://dev.to/gnana_6392e836fd500a957dc/ai-engineer-skills-companies-want-in-2026-3449-posting-analysis-5f9l) (community post; InterviewStack job board, active postings May 2026; synonyms merged, each posting counted once per skill; the author says staffing re-posts inflate counts and the normaliser split "llm" and "llms").
  - [365 Data Science, AI Engineer job outlook](https://365datascience.com/career-advice/career-guides/ai-engineer-job-outlook-2025/) (education vendor; 903 Glassdoor US postings after cleaning, though titled "1,000"; no matching rules or limits stated; its chart and text disagree on AWS and Azure).
  - [KDnuggets, the AI skills that show up in job postings](https://kdnuggets.com/the-ai-skills-that-actually-show-up-in-job-postings-right-now) (secondhand; the 390-posting analysis behind the 56/50/26% is not named; mixed denominators).
  - [Hacker News job posts, 32,924 posts (Gitconnected post)](https://levelup.gitconnected.com/the-10-ai-skills-employers-actually-asked-for-in-32-924-hacker-news-job-posts-and-prompt-239a8272445d) (community post; read from a search snippet only; Hacker News skews to startups) and [jobspipe MCP tracker](https://jobspipe.dev/technologies/model-context-protocol) (tracker; snippet only).
  - Vietnam postings: [ITviec, AI engineer intern (Innotech)](https://itviec.com/it-jobs/good-english-ai-engineer-intern-ai-agents-llm-rag-innotech-vietnam-corporation-3040), [ITviec, AI engineer Python LLM RAG LangChain (Cloudteam)](https://itviec.com/it-jobs/ai-engineer-python-llm-rag-langchain-ai-agents-cloudteam-4320), [TopDev, fresher AI engineer (Shinhan Securities)](https://topdev.vn/viec-lam/prompt-llm-nlp-ai-engineer-fresher-shinhan-securities-2046742), [TopDev, junior AI engineer (Namitech)](https://topdev.vn/viec-lam/junior-ai-engineer-agentic-voicebot-chatbot-namitech-2090927) (job boards; snippets only).
  - Serving: individual postings on [agentic-engineering-jobs.com](https://agentic-engineering-jobs.com/jobs/vllm) (aggregator; too few to estimate a share). See also `findings/quantization-in-practice`.
- **Limits:**
  - Samples are US-centred or board-specific; none is Vietnam, and none separates entry level (only one source says 2.5% of postings ask 0-2 years).
  - Keyword matching is undocumented in two of three; "RAG" or "evaluation" may be matched very differently across them, which probably explains the spread.
  - A skill's share in postings is not its importance to a hire: a mention may be one item in a long list.
  - The Hacker News and MCP figures come from search snippets and were not checked on the page.
  - Searches did not find LinkedIn, Indeed or labour-market datasets with per-skill AI-engineer counts, or any count for hallucination detection or vLLM by name.
- **Checked:** 2026-11-18
