# Which model tests run in CI

- **Question:** How do machine-learning projects split tests between pull-request CI and heavier runs, when real weights, data or GPUs are not available in CI?
- **Checked:** 2026-11-05

## Finding

- **Two tiers.** Hugging Face Transformers runs model tests without `@slow` on every pull request, and slow tests on a nightly schedule. A test is `@slow` if it downloads weights, loads a large dataset or takes more than a few seconds.
- **The fast tier still runs the model code**, using tiny configs with random weights, small enough to "finish in seconds on CPU". It checks behaviour and shapes, not output quality.
- **Numerical correctness belongs to the slow tier, with real weights.** Tiny models are "a last resort" for integration tests: "Use original pretrained weights, when possible, to catch real numerical regressions."
- **Determinism and hardware.** Generation tests use `do_sample=False`. Results vary slightly across GPU generations, so expected values are registered per device.
- **The slow tier runs on a schedule, not by memory** (nightly in Transformers; Diffusers has a daily cron with `RUN_SLOW` and `RUN_NIGHTLY`).

Not from a source (the checker's inference): skipping real-weight tests in pull-request CI is normal. Having no fast tier that runs the model code on CPU is the gap, as is a slow tier that only runs when someone remembers it. A small project with no GPU runner can treat a manual cloud run as its slow tier if a rule says when it must run.

## Sources

- [Transformers: writing model tests](https://huggingface.co/docs/transformers/testing) (official docs).
- [Transformers v4.18 testing docs](https://huggingface.co/docs/transformers/v4.18.0/en/testing) (official docs, old version).
- [Diffusers nightly workflow, hosted copy](https://huggingface.co/iosca/Omnieraser/blob/main/diffusers/.github/workflows/nightly_tests.yml) (a copy, not the canonical repository; read only through a search summary).

## Limits

One large open-source project and its sibling, with funded GPU runners; no source covers a solo project without them. No general study or standards body was found.
