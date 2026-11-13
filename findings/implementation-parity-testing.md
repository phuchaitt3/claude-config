# Implementation parity testing: how many samples, how strict

**Question:** When a model pipeline is re-implemented (a port, a new inference engine), how many samples and how many settings does a parity test need, and what counts as a match?

**Finding:**
- No source sets a sample count. The published parity and verification setups use a handful of fixed short prompts, a modest number of greedy tokens (32 in one worked example), and compare the chosen token (and top-k ids) at each step. The exact count is a project decision.
- Exact equality is not required by the guidance found. Modular's logit-comparison docs say exact equality of logit values is not needed and use mean absolute error against a tolerance and cosine distance; the Transformers add-a-model guide asks for a forward pass that matches the original checkpoint, plus model tests and integration tests as separate steps.
- Greedy decoding is not stable across batch shape, GPU count or GPU model: logits change with what else is in the batch, and near-tie argmax flips send two runs down different sequences. A paper on this finds results differ under greedy decoding when batch size, number of GPUs or GPU version changes. So a parity test fixes the batch size (batch 1 is the usual choice) and, where per-step comparison matters, teacher-forces the reference tokens (NVIDIA's few-layer validation).
- A divergence is judged against the noise floor, not a fixed tolerance: AWS Neuron's accuracy guide compares the target with HF in FP32 and HF in BF16, and treats a top-1 difference where the top two logits are very close as expected.
- Checker's own inference (not stated by the sources): with exact token match as the bar, a systematic fault (wrong prompt, mask or scale) shows on the first few samples, so tens of samples are ample; extra values of a tuned setting that share one code path add little beyond one non-zero value plus the off case. A match rate near the batched-vs-unbatched noise floor of the same stack (about 93% in one measurement) is noise, a match at 50% or below is a systematic difference (as when the answers came from other package versions).

**Sources:**
- [NVIDIA TensorRT Edge-LLM, few-layer numeric validation](https://nvidia.github.io/TensorRT-Edge-LLM/latest/developer_guide/testing/few-layer-validation.html) (vendor docs).
- [Llama-3.2-1B verification subsystem](https://raw.githack.com/tonyjie/mlir-air/llama32_1b-verify-pr/programming_examples/llama32_1b/docs/detail/VERIFICATION.html) (community project, one prompt, 32 greedy tokens).
- [Modular MAX, logit comparison](https://docs.modular.com/max/develop/logit-comparison/) (vendor docs).
- [Transformers, how to add a model](https://huggingface.co/docs/transformers/v4.26.1/add_new_model) (official docs).
- [AWS Neuron, debugging accuracy issues](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/vllm-neuron/docs/model-dev/accuracy-debugging-guide.html) (vendor docs).
- [Give Me FP32 or Give Me Death?](https://arxiv.org/html/2506.09501v1) (preprint on greedy-decoding variation with batch size, GPU count and GPU version).
- [vLLM forum, numerical difference between vLLM and Hugging Face logprobs](https://discuss.vllm.ai/t/numerical-difference-between-vllm-logprobs-and-huggingface-logprobs/151) (community post).

**Limits:** Snippets from search results only, not the full pages. I did not read the Transformers repository's own test files, so its prompt counts and tolerances are not covered. Several sources are vendor docs or forum posts. Nothing found studies the sample size of a parity test statistically.

**Checked:** 2026-11-12
