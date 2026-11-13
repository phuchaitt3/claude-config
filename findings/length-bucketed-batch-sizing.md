# Batch sizing when batches are sorted or bucketed by length

- **Question:** When batches are formed by sorting or bucketing inputs by length (to cut padding), how do tools and papers pick the batch size, and what sample should a timing sweep use so it reflects the real batches?
- **Finding:**
  - **Grouping by length is established practice.** Hugging Face `Trainer` has `group_by_length` (`LengthGroupedSampler`), which reads every length in the dataset to build batches of similar length (forum answer: grouping over a subset only is not implemented). Lhotse/NeMo use duration buckets whose bins are estimated from the dataset's own length distribution (`lhotse cut estimate-bucket-bins`, `estimate_token_bins.py`). For offline LLM generation, sorting prompts before `llm.generate` is reported to speed up vLLM by 7–17% (Hugging Face blog, similarity sort with length grouping as a side effect).
  - **With buckets, the batch size is set per bucket, not once.** NeMo's OOMptimizer binary-searches, for each length bucket, the largest batch that fits (up to 90% of GPU memory by default) and writes a per-bucket list (`bucket_batch_size=[352,308,280,...]`). The Canary-1B paper (arXiv 2503.05931) reports that this raised the mean batch size 3.4× (about 5× with 2D buckets) and cut padding from 57–59% (fixed batch size) to 4.5–19%. It targets memory (largest that fits), not a throughput knee.
  - **The size of the sorting pool changes the result.** Sorting chunks of 128 prompts gave +11.7%, chunks of 256 +14.8%, and the full 768 prompts +17.3% (Hugging Face blog, batch 32). So a measurement made on a smaller sorted pool than the real run understates what sorting does at that batch size.
  - **Checker's inference (no source found):** no source describes a throughput sweep over batch sizes that times a subsample of a length-sorted run. Where batches depend on sorting, the faithful proxy is to build the real run's batches (sort all inputs, pack at each candidate size) and time a sample of those batches, picked at evenly spaced positions in the sorted order. That is cluster sampling with probability proportional to batch size, so the run-level estimate is the mean of the timed batches' seconds per item. Timing a sorted small sample instead packs inputs of very different lengths together and overstates padding at larger batch sizes.
- **Sources:**
  - NVIDIA NeMo, Lhotse dataloading (bucketing, OOMptimizer; official docs): https://docs.nvidia.com/nemo/speech/latest/dataloaders.html
  - Training and inference efficiency of encoder-decoder speech models (Canary-1B; paper, arXiv 2503.05931v1): https://arxiv.org/abs/2503.05931
  - "Sort your prompts" (Hugging Face blog, vLLM 0.27 on MI300X, 768 prompts, 3 repeats): https://huggingface.co/blog/badaoui/sort-your-prompts
  - Hugging Face forum on `group_by_length` (community): https://discuss.huggingface.co/t/how-to-implement-trainers-group-by-length-in-pytorch/9232
  - Related entries: [llm-batch-size-selection](llm-batch-size-selection.md) (sweep and pick rule), [llm-inference-memory-calibration](llm-inference-memory-calibration.md) (padding, where a bigger batch stops paying).
- **Limits:**
  - NeMo's per-bucket sizing is for training and maximises memory use; no source here picks a per-bucket size by throughput.
  - The Hugging Face blog sorts by similarity, not by length, on MoE models with continuous batching (no padding), so its gains measure batch composition, not padding; the pool-size trend is the transferable part.
  - The batch-sampling proxy is the checker's own design from sampling theory; it is not validated by any source and should be checked against a full-run timing.
- **Checked:** 2026-11-11
