---
topic: ocr-vietnamese-character-coverage
area: ML systems
question: Can PaddleOCR's stock recognition models read Vietnamese? (Separate entry: no other entry covers OCR models.)
checked: 2026-11-27
review_months: 12
status: current
---
# OCR recognisers and Vietnamese characters

- **Question:** Can PaddleOCR's stock recognition models read Vietnamese?

- **Finding:**
  - PaddleOCR accepts `lang="vi"`: `vi` is in `LATIN_LANGS`, and for PP-OCRv5 a Latin language selects `latin_PP-OCRv5_mobile_rec` (source files, main branch; latest release v3.7.0, 2026-06-11).
  - A recogniser can only output characters listed in the `character_dict` of its `inference.yml`. On a sample of 54,649 non-space characters of Vietnamese prose (50 pages of 1910 to 1925 prints), the shipped dictionaries lacked 13.0% (`latin_PP-OCRv5_mobile_rec`, 770 entries) and 12.6% (`PP-OCRv6_medium_rec` and `PP-OCRv6_small_rec`, 1,747 entries). Most missing characters are vowels carrying two marks (ế, ờ, ấ, ạ, ớ, ả, ộ). Measured by the checker from the downloaded files.
  - So language support listed in the library does not mean the model can write the language: check the dictionary before spending a run. On the same kind of text, these models' character error rate cannot go below the missing share (inference from the two lines above).

- **Sources:**
  - Language groups (source): https://github.com/PaddlePaddle/PaddleOCR/blob/main/paddleocr/_utils/langs.py
  - Model choice per language (source): https://github.com/PaddlePaddle/PaddleOCR/blob/main/paddleocr/_pipelines/ocr.py
  - Model files with `inference.yml` (official weights): https://huggingface.co/PaddlePaddle/latin_PP-OCRv5_mobile_rec , https://huggingface.co/PaddlePaddle/PP-OCRv6_medium_rec , https://huggingface.co/PaddlePaddle/PP-OCRv6_small_rec

- **Limits:** No model was run. Server variants of the recognisers, third-party or fine-tuned Vietnamese models (for example a PaddleOCR detector with another recogniser) were not checked. The 12 to 13% figure is for old Vietnamese prints; modern text may differ somewhat. Weights can change in a later release.

- **Evidence strength:** strong for the dictionary content (read from the shipped files); the effect on error rate is arithmetic, not a measured run.

- **Checked:** 2026-11-27
