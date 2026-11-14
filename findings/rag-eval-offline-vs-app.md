# RAG evaluation: separate offline scripts or the running application?

- **Question:** Where should a RAG pipeline be evaluated: in separate offline evaluation scripts, or through the application (production)? And which result belongs on a resume?
- **Finding:**
  - **Both, for different jobs; guides call them complementary.** Offline evaluation runs a fixed, labelled question set outside live traffic, on every meaningful change to retrieval, prompts or the model. Online evaluation samples live traffic (one guide says 1–5%) and catches what a fixed set misses: corpus drift, shifting question styles, the long tail of phrasings nobody wrote. One guide puts it as: offline catches what you broke, online catches what broke without anyone touching anything.
  - **Retrieval is scored on its own, before the final answer.** Several guides say to evaluate retrieval (Recall@k, Precision@k; nDCG for a reranker against a no-reranker baseline) and generation separately: an end-to-end answer score shows the system is failing but not which stage. Using one end-to-end metric alone is listed as an anti-pattern. End-to-end checks still confirm the user-visible result.
  - **Keep scripts honest.** Change one variable at a time with corpus, queries, generator and judge fixed; version the question set so runs stay comparable; include unanswerable questions; build the set from real queries where they exist, with synthetic questions as a backstop.
  - **The two feed each other.** Production failures are added to the offline set; if offline scores rise while online ones fall, the set has a coverage gap.
  - *Checker's inference (not stated by the sources):* a fixed-set run through the real application is a third kind, an integration check. It can disagree with a script that uses a stand-in for a component (a different text extractor, a different keyword ranker, a different scorer), and the disagreement is the point: it finds defects the script cannot. A result should say which of the two produced it ("benchmark" or "through the app"); a resume bullet that quotes a script's number as the application's accuracy reads wider than the evidence.
- **Evidence strength:** common practice among vendor guides that agree with each other; no standards body, official documentation or controlled study was read. The percentages and set sizes (1–5% sampling, 20–300 questions) are rules of thumb from single blogs.
- **Sources:**
  - [Offline and online RAG evaluation](https://apxml.com/courses/optimizing-rag-for-production/chapter-6-advanced-rag-evaluation-monitoring/rag-offline-online-evaluation) (course site)
  - [Offline vs online LLM evaluation: what each catches](https://galtea.ai/blog/offline-vs-online-llm-evaluation-what-each-catches-what-each-misses) (vendor blog)
  - [How to test a RAG pipeline](https://www.braintrust.dev/articles/how-to-test-rag-pipeline) (vendor blog)
  - [What is RAG evaluation?](https://arize.com/glossary/rag-evaluation/) (vendor glossary)
  - [RAG evaluation, LLM-as-a-judge guide](https://evidentlyai.com/llm-guide/rag-evaluation) (vendor guide)
  - [RAG evaluation framework for production AI systems](https://layerlens.ai/blog/rag-evaluation-framework-for-production-ai-systems) (vendor blog)
  - [RAG evaluation complete guide](https://www.getmaxim.ai/articles/rag-evaluation-a-complete-guide-for-2025/) (vendor blog)
- **Limits:** All sources are tool vendors or blogs selling evaluation products; search returned no Pinecone, Anthropic, Microsoft or Google guide. Read through search summaries, not every page in full. A claim in one result that retrieval explains about 60% of end-to-end quality variance cites a study that could not be verified and is not used. Nothing found says how a hiring reader treats a benchmark figure against an application figure; see `resume-benchmark-context`.
- **Checked:** 2026-11-14
