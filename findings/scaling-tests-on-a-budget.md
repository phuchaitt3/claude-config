# Scaling tests on a small budget

- **Question:** How do teams learn how a system behaves at a much larger size or load without paying for a production-size environment?
- **Checked:** 2026-11-01

## Finding

- **Find the knee, not a pass.** A capacity test should show where the system breaks and how it degrades, not only that it passes at one size (Gatling). Run it in increasing steps before any full-size run (RadView).
- **Scaled-down environments do not scale linearly.** An environment at 50% of production does not give 50% of its performance; one smaller part (less memory on one server) can degrade the whole system (Ten10 whitepaper). Results from a downsized environment cannot simply be extrapolated; modelling helps but is not always reliable. Horizontal scaling extrapolates more predictably than vertical, and a one-node test of a many-node system can behave quite differently (CMG). The mitigation is to find the knee in the small environment with incremental load and treat any projection beyond it as an early risk signal, not a result (CMG, Ten10).
- **Keep the load profile honest.** Cutting think times or shortening sessions (500 users for two minutes instead of 5,000 for an hour) changes the profile and invalidates capacity conclusions (practitioner article). A small test database can hide query problems that appear at full size.
- **Replace paid or fragile dependencies with mocks or simulators.** Mocks avoid per-call charges and rate limits and keep the test from overloading partner systems (Beeceptor, SmartBear). They should be configured with realistic latency and error responses, ideally recorded from the real service. For LLM APIs, simulators model time to first token, inter-token delay, token counts and injected 429/5xx errors behind a provider-compatible endpoint (LLMSim, MockLLM, Speedscale); one company reports replacing live LLM calls in load tests with a mock layer at 16,000 requests a minute (Salesforce Engineering). A mock measures your own system's capacity, not the provider's latency, quality or cost; those still need a small run against the real provider (Speedscale).
- **When cloud is needed, make it short-lived.** Provision test infrastructure at the start of a run and decommission it immediately after (AWS load-testing guidance); ephemeral environments are destroyed on a lifecycle trigger (test complete, time window expired). Spot instances cut compute price sharply, but interruptions lengthen runs and need extra instances, so real savings are below the headline discount (Synopsys analysis). Ephemeral environments are not cheaper by default; cost depends on size and lifetime.
- **Approximate search: compare at matched quality.** Sweep the quality knob and compare latency at equal recall against an exact scan, on your own data and filters (ANN-Benchmarks and VectorDBBench practice, as described by a vendor).
- Checker's inference (not stated by the sources): for a solo developer on a laptop, the cheapest path that still teaches scaling is fakes or simulators for every paid dependency, synthetic data ramped to the machine's memory limit, a recorded knee, and at most one short, torn-down cloud run to check the largest step.

## Sources

- [Gatling, From 1 to n (capacity planning checklist)](https://gatling.io/checklists/from-1-to-n) (vendor docs).
- [RadView, How to load test successfully](https://www.radview.com/blog/a-step-by-step-guide-on-how-to-load-test-successfully/) (vendor blog).
- [CMG, Performance assessments in scaled-down environments](https://www.cmg.org/2017/03/performance-testing/) (professional body article).
- [Ten10 / Scale Factory, Performance testing in non-representative environments](https://scalefactory.com/performance-testing-in-non-representative-environments-10-key-factors-for-consideration/) (consultancy whitepaper).
- [Software Test Pro, think times and scaled-down sessions](https://softwaretestpro.com/?p=4103) (practitioner article).
- [Beeceptor, API mocking for performance tests](https://beeceptor.com/docs/api-service-mocking-for-performance-tests) and [SmartBear, 4 ways to load test your API](https://smartbear.com/blog/4-ways-to-load-test-your-api) (vendor docs and blog).
- [Speedscale, LLM simulation](https://docs.speedscale.com/guides/mocking/llm-simulation/), [LLMSim README](https://docs.rs/crate/llmsim/0.2.3/source/README.md), [MockLLM](https://pypi.org/project/mockllm/) (vendor docs, open-source tools).
- [Salesforce Engineering, mock layer for LLM load testing](https://engineering.salesforce.com/?p=8028) (company engineering blog).
- [Synopsys, cost strategies for cloud testing (spot instances)](https://qacf-www.synopsys.com/blogs/chip-design/strategies-to-optimize-costs-cloud-testing.html) and [Northflank, ephemeral environments and cost](https://northflank.com/blog/how-do-ephemeral-environments-reduce-infrastructure-costs) (vendor blogs).
- [Zilliz, ANN-Benchmarks and VectorDBBench](https://zilliz.com/ai-faq/what-role-do-tools-like-annbenchmark-for-algorithmlevel-comparison-and-vectordbbench-for-full-database-benchmarking-play-and-how-does-each-assist-in-evaluating-different-aspects-of-performance) (vendor FAQ).

## Limits

No standard body covers this; the sources are vendors, a consultancy and a professional-body article from 2017. The mock and simulator sources sell or build such tools. The Salesforce figure is self-reported. Spot discounts and environment costs vary by provider and were not checked against price lists. The AWS teardown guidance was quoted through a search summary, not read directly.
