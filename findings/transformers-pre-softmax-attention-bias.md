---
topic: transformers-pre-softmax-attention-bias
area: ML systems
question: Can a user of Hugging Face Transformers add a bias to pre-softmax attention scores without replacing the attention layer's forward method?
checked: 2026-11-27
review_months: 6
status: current
---
# Adding a pre-softmax attention bias in Hugging Face Transformers

- **Question:** Can a user add a bias to pre-softmax attention scores without replacing the attention layer's forward method?
- **Finding:**
  - **Yes, there are supported routes, so "the scores cannot be reached" is wrong.**
  - **The attention mask is added to the scores before softmax** in the eager function (Qwen2, v4.57.6: `attn_weights = attn_weights + causal_mask`, then softmax).
  - **A custom attention function can be registered** (`AttentionInterface.register`, then `attn_implementation=...`). It receives module, query, key, value, attention_mask and extra keyword arguments passed to the model's forward. A mask function must also be registered, or `attention_mask` arrives as None.
  - **A custom 4D attention mask can be passed to `forward()`** (Hugging Face community blog, Jan 2024); its example needs `position_ids` and uses `model.forward()`, not `generate()`.
  - **`output_attentions` returns post-softmax weights**, so that output does not expose the scores.
  - **Checker's inference:** a bias that depends only on token positions (not on the score values) can be written as an additive float 4D mask. Not run; behaviour of a float mask through `generate()`, sdpa and flash paths not checked. A bias that depends on the scores, or that needs per-layer strength or logging, is simpler with a custom attention function.
- **Sources:**
  - https://raw.githubusercontent.com/huggingface/transformers/v4.57.6/src/transformers/models/qwen2/modeling_qwen2.py
  - https://huggingface.co/docs/transformers/v4.57.1/attention_interface
  - https://huggingface.co/blog/poedator/4d-masks
  - https://huggingface.co/docs/transformers/main_classes/output
- **Evidence strength:** primary source code and official docs for the first three claims and the last sourced one; the 4D-mask route rests on a community blog; the equivalence is inference, untested. Pages read through a fetch summariser, not line by line.
