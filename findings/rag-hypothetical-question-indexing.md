# Indexing generated questions instead of chunks in RAG

- **Question:** Is it an established RAG practice to embed LLM-generated questions for each chunk, match the user's query against those questions, and return the parent chunk?
- **Finding:**
  - Yes. LangChain's official MultiVectorRetriever guide lists "hypothetical questions" as one of its strategies: an LLM writes questions each document can answer, and those are embedded "along with, or instead of, the document"; a hit returns the parent document through a `doc_id`.
  - It is described as a variant of HyDE: HyDE has the LLM write a hypothetical answer to the query, while this approach generates questions per chunk at index time and matches question to question (GraphRAG reference; Manning, *Essential GraphRAG*).
  - The stated benefit is matching the user's intent (questions look like questions). *Checker's inference:* the weakness is coverage. A query unlike any generated question can miss its chunk, which is why guides offer indexing the chunk text alongside the questions.
- **Sources:**
  - LangChain docs, "How to retrieve using multiple vectors per document" (official docs): https://python.langchain.com/docs/how_to/multi_vector
  - GraphRAG.com, "Hypothetical Question Retriever" (community reference): https://graphrag.com/reference/graphrag/hypothetical-question-retriever/
  - Manning, *Essential GraphRAG*, chapter 3 preview (book): https://www.manning.com/preview/essential-graphrag/chapter-3
  - LangChain OpenTutorial, MultiVectorRetriever (community tutorial): https://langchain-opentutorial.gitbook.io/langchain-opentutorial/10-retriever/07-multivectorretriever
- **Related:** testing such an index with questions from the same generator flatters it; see [rag-retrieval-eval-without-benchmark](rag-retrieval-eval-without-benchmark.md).
- **Limits:** read through search summaries, not the full pages. No peer-reviewed comparison of question-only against chunk-plus-question indexing was found, and no LlamaIndex page for the pattern.
- **Checked:** 2026-11-09
