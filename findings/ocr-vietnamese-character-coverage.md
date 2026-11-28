---
topic: ocr-vietnamese-character-coverage
area: ML systems
question: What reads printed Vietnamese pages (Tesseract, PaddleOCR, small vision-language models)? (Separate entry: no other entry covers OCR models.)
checked: 2026-11-28
review_months: 12
status: current
---
# OCR for Vietnamese pages

- **Question:** What reads printed Vietnamese pages, and can PaddleOCR's stock recognition models do it?

- **Finding:**
  - PaddleOCR accepts `lang="vi"`: `vi` is in `LATIN_LANGS`, and for PP-OCRv5 a Latin language selects `latin_PP-OCRv5_mobile_rec` (source files, main branch; latest release v3.7.0, 2026-06-11).
  - A recogniser can only output characters listed in the `character_dict` of its `inference.yml`. On a sample of 54,649 non-space characters of Vietnamese prose (50 pages of 1910 to 1925 prints), the shipped dictionaries lacked 13.0% (`latin_PP-OCRv5_mobile_rec`, 770 entries) and 12.6% (`PP-OCRv6_medium_rec` and `PP-OCRv6_small_rec`, 1,747 entries). Most missing characters are vowels carrying two marks (ế, ờ, ấ, ạ, ớ, ả, ộ). Measured by the checker from the downloaded files.
  - So language support listed in the library does not mean the model can write the language: check the dictionary before spending a run. On the same kind of text, these models' character error rate cannot go below the missing share (inference from the two lines above).

- **Common approaches and candidate models (checked 2026-11-28):**
  - **No agreed standard was found** for OCR of Vietnamese PDFs. The searches returned small self-run benchmarks on different data that disagree, so a project measures on its own pages (project READMEs and preprints).
  - Printed clean pages: small projects report Tesseract `vie` as adequate, with CER near 0 to 2% on generated or clean pages (project READMEs; tiny test sets, not old or scanned books).
  - `PaddleOCR-VL-1.6`: a vision-language document parser of about 0.96B parameters, Apache 2.0, released 2026-05-28; its page tags say multilingual but do not list Vietnamese. As a generative model it is not limited by the recogniser dictionaries below (inference).
  - `SenOCR-Vi`: a Vietnamese fine-tune of PaddleOCR-VL-1.6, Apache 2.0. Its card reports a Vietnamese composite of 82.83 against 80.90 for the base model and 85.60 for the 5B `chandra-ocr-2`, on a 160-page MDPBench population; no Qwen model is in that table (self-reported model card, other scores taken from the leaderboard).
  - `Vintern-1B-v3_5`: about 0.9B parameters, CC BY-NC 4.0 (non-commercial); the card gives no Vietnamese CER.
  - `Qwen2.5-VL-3B-Instruct`: released January 2025. A FastOCR paper says it is under the Qwen Research License; the fetched model page named no licence (check the licence file before using it in a product). No Vietnamese OCR result for it was found. For fp16 on a T4, see `precision-across-model-sizes`.
  - MDPBench (2026) covers 17 languages including Vietnamese; it reports that open-source parsers drop on photographed and non-Latin pages (paper, read as a search summary).

- **Sources:**
  - Language groups (source): https://github.com/PaddlePaddle/PaddleOCR/blob/main/paddleocr/_utils/langs.py
  - Model choice per language (source): https://github.com/PaddlePaddle/PaddleOCR/blob/main/paddleocr/_pipelines/ocr.py
  - Candidate model cards (vendor, read 2026-11-28): https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.6 , https://huggingface.co/VietAlphaLabs/SenOCR-Vi , https://huggingface.co/5CD-AI/Vintern-1B-v3_5 , https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct
  - MDPBench (preprint): https://arxiv.org/abs/2603.28130 ; Vietnamese document analysis survey (preprint): https://arxiv.org/html/2506.05061
  - Small self-run benchmarks (project READMEs): https://github.com/nrl-ai/nom-vn , https://github.com/khanhlinh-innomation/vlm-handwriting-ocr
  - Model files with `inference.yml` (official weights): https://huggingface.co/PaddlePaddle/latin_PP-OCRv5_mobile_rec , https://huggingface.co/PaddlePaddle/PP-OCRv6_medium_rec , https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec

- **Limits:** None of the candidate models was run; no source covers Vietnamese prints of the early twentieth century. No model was run. Server variants of the recognisers, third-party or fine-tuned Vietnamese models (for example a PaddleOCR detector with another recogniser) were not checked. The 12 to 13% figure is for old Vietnamese prints; modern text may differ somewhat. Weights can change in a later release.

- **Evidence strength:** strong for the dictionary content (read from the shipped files); the effect on error rate is arithmetic, not a measured run.

- **Checked:** 2026-11-28 (the character-dictionary measurement is from 2026-11-27)
