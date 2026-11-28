---
topic: ocr-default-in-pdf-ingestion
area: ML systems
question: Do PDF ingestion tools run OCR by default, and on which pages? (Separate entry: the other OCR entries cover error rates and models, not defaults.)
checked: 2026-11-28
review_months: 12
status: current
---
# OCR defaults in PDF ingestion

- **Question:** Is OCR on by default, and on which pages?
- **Finding:**
  - Docling: `do_ocr` defaults to true, and the default mode reads layout regions, dropping regions that hold only text-layer cells; full-page OCR is opt-in (source file; the `do_ocr` value was read as a summary).
  - NVIDIA RAG Blueprint 2.6: OCR on by default (official docs, search summary).
  - Unstructured: default strategy `auto` chooses by document; the page does not say when that means OCR (official docs).
  - OCRmyPDF: by default stops on a page that already has text; skipping such pages is opt-in (official docs).
  - A plain text-layer loader (LangChain PyPDFLoader) does no OCR (search summary).
  - Inference: no single standard; full document pipelines tend to enable OCR and limit it to pages without usable text. A scan-only page is otherwise lost silently.
- **Sources:**
  - https://github.com/docling-project/docling/blob/main/docling/datamodel/pipeline_options.py
  - https://docs.nvidia.com/rag/2.6.0/nemoretriever-ocr.html
  - https://docs.unstructured.io/open-source/concepts/partitioning-strategies
  - https://ocrmypdf.readthedocs.io/en/latest/advanced.html
- **Limits:** a few tools, no survey; Open WebUI's default could not be confirmed. Partly read through a summarising fetch tool and a research subagent.
- **Evidence strength:** moderate for the tools named; weak as a claim about the field.
