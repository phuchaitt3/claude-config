---
name: scaling-test
description: Load before measuring how something behaves at a larger size than today's data (a load test, a benchmark of a store or index, a "does it still work at 100x" run), or before generating synthetic data to do so. How to ramp in steps on one machine, check the memory budget first, compare at matched quality, label synthetic data, and ask before any cloud spend.
---

# Testing scaling problems on a small budget

User's decision, 2026-11-01, after a vector-store experiment in a RAG project could only compare two stores on 164 real chunks. Used with `workflow:experiment` (which decides what to compare and by when) and `workflow:adr` (numbers go in a measurement note, the ADR keeps one line).

## Steps

1. **State the question and the knee you expect.** What size or rate do you expect to break first (memory, latency, recall, build time)? A test with no expected breaking point only confirms that small sizes work. (standard: Gatling capacity-planning checklist, find where the system breaks and how it degrades, not only that it passes; checked 2026-11-01)
2. **Do the memory and disk arithmetic first,** on paper, and compare it with what the machine can give the test (RAM, the container limit, free disk). Put the numbers in the test notes. If the target size does not fit, say so before starting; "does not fit on a small machine" is itself a result. Check the machine (`Get-CimInstance Win32_ComputerSystem`, free disk) instead of assuming.
3. **Ramp in steps,** for example 10x, 30x, 100x of today's size, and stop at the first step that fails or bends the curve. Never jump to the target size. Watch memory while it runs, set a hard memory limit on each container, and stop at a threshold you chose in advance. A scaled-down environment does not scale linearly, so read the curve and do not extrapolate it far. (standard: CMG, scaled-down environments; RadView, run scaling tests before full-size runs; checked 2026-11-01)
4. **Warm up, then measure the same way for both sides.** Run `ANALYZE` (or the equivalent) after a bulk load, let index builds finish, run a warm-up pass, and discard it. Same inputs, same rate, same machine state, one path at a time. A result that flips after a warm-up step was an artefact: record it as one and do not use it.
5. **Compare at matched quality.** For search and other approximate systems, sweep the quality knob (for example `ef_search`) and compare latency at the same recall, not one setting per side. Measure recall against an exact scan, and use your own filters and your own data shape. (standard: ANN-Benchmarks and VectorDBBench practice, vendor-run and vendor-adjacent sources, so check the method on your own data; checked 2026-11-01)
6. **Label what is synthetic,** in the table and the note: copied rows, random vectors and generated queries are not real data. Copies of the same vectors are easier than real data for an approximate index. Real queries and real distributions need real data.
7. **Report limits next to the numbers:** machine, sizes, run length, number of samples, what was not tested. Tail percentiles (p99) need enough samples to mean anything.
8. **Clean up.** Delete the containers, volumes and test data you created, and release any claimed resource (for example the Compose stack in a multi-chat project).

## Ask first

Anything that costs money (a cloud machine, a paid tier, a managed database) or runs longer than the working rules' threshold needs the user's yes first, with the sizes, the price limit and what the test will show. A local run that may exhaust the machine's memory needs the ramp and limits above, and a message to the user before the largest step.

## Sources

- Gatling, From 1 to n (capacity planning): https://gatling.io/checklists/from-1-to-n
- CMG, Performance assessments in scaled down environments: https://www.cmg.org/2017/03/performance-testing/
- RadView, How to load test successfully: https://www.radview.com/blog/a-step-by-step-guide-on-how-to-load-test-successfully/
- Zilliz, ANN-Benchmarks and VectorDBBench: https://zilliz.com/ai-faq/what-role-do-tools-like-annbenchmark-for-algorithmlevel-comparison-and-vectordbbench-for-full-database-benchmarking-play-and-how-does-each-assist-in-evaluating-different-aspects-of-performance
- pgEdge, pgvector HNSW build memory: https://docs.pgedge.com/pgvector/v0-8-5/hnsw/
