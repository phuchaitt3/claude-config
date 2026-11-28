---
topic: ocr-cer-acceptable-and-retrieval
area: ML systems
question: What OCR character error rate is acceptable, in general and for retrieval or RAG?
checked: 2026-11-28
review_months: 12
status: current
---
# Acceptable OCR error rates

- **Question:** What error rate is acceptable, and what does it do to retrieval?
- **Finding:**
  - No agreed standard. Holley (2009), a rule of thumb for newspaper digitisation: 98 to 99% accurate is good, 90 to 98% average, below 90% poor; whether characters or words was not settled.
  - Classic IR with simulated errors (Portuguese): significant retrieval loss from 5% WORD error rate.
  - RAG studies: character error rate alone predicts retrieval quality poorly; error type and reading order matter.
  - One Vietnamese old-book study: off-the-shelf Tesseract CER 0.14, fine-tuned 0.09, commercial or LLM readers 0.04 to 0.07.
  - Inference: no source sets 0.05; a project target is a choice. Judge by retrieval hit rate on OCR text against ground-truth text.
- **Sources:**
  - https://www.dlib.org/dlib/march09/holley/03holley.html
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC7148068
  - https://arxiv.org/html/2412.02592
  - https://arxiv.org/html/2410.13305
- **Limits:** nothing covers Vietnamese retrieval on early-20th-century print; two sources are preprints; read by a research subagent.
