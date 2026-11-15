---
topic: eval-sample-size
area: Research methods
question: How many test questions or timed requests does an evaluation need, and is 30 or about 200 too small?
checked: 2026-11-15
review_months: 24
status: current
---
# How many test samples a reliable evaluation needs

- **Question:** How many test questions (accuracy, retrieval hit rate) or timed requests (latency) does an evaluation need before its number is reliable, and is a set of 30 or about 200 too small?
- **Finding:**
  - **No fixed count; the standard is to report the uncertainty and size the set for the precision the claim needs.** Anthropic's "Adding error bars to evals" (Miller, 2024) asks every eval score to carry a standard error and a 95% interval (score ± 1.96 SE), and sizes the set by power analysis: confidence level, the smallest difference worth detecting, and the metric's variance. A set is "big enough" when the interval is narrower than the difference the claim depends on.
  - **For a proportion (accuracy, Hit@k) the half-width of a 95% interval is about 1.96·√(p(1−p)/n).** At p = 0.9: ±10.7 points at n = 30, ±5.9 at 100, ±4.1 at 200, ±2.9 at 400, ±1.9 at 1,000 (checker's arithmetic). Scores near 100% have narrower intervals but need a Wilson or bootstrap interval, not the normal one; Bowyer et al. (2025) argue the normal (CLT) interval misleads below a few hundred items.
  - **Comparing two systems on the same questions needs far fewer items than measuring one in absolute terms**: a paired test uses the per-question differences, so a large, consistent gap (tens of points, or seconds against a small spread) is settled at n = 30, while a 1–2 point gap may need thousands.
  - **Clustered items shrink the effective size.** Several questions from one document or one book are not independent; plain intervals come out too narrow, so resample by cluster, and a single-source set does not generalise beyond that source whatever its size (see `rag-eval-confidence-intervals`).
  - **Information retrieval's long-standing rule: 25 topics minimum, 50 for stable system rankings** (Buckley and Voorhees, SIGIR 2000; Voorhees on TREC-6: rankings from 5–10 topics are unstable, 25+ stable). Later work argues for more (Carterette et al. 2006: about 200 with shallow judging; Sparck Jones and van Rijsbergen: 250 acceptable, 1,000 for reliable) and for formal sample-size design per metric.
  - **Latency: the count needed depends on the percentile.** A percentile needs enough samples beyond it to exist at all: p99 needs at least 100 samples for one data point past it and p99.9 at least 1,000; a stable p99 needs several hundred to thousands. A median is stable from a few dozen samples when the spread is small; give an order-statistic or bootstrap interval. Load-test vendors warn that p99 from a short test is noise. *Checker's inference:* 30 timed requests support a median and a rough p90, not a p99.
  - **Size is not the only reliability question.** Synthetic (LLM-generated) questions and a single source document bias the score upward regardless of n (`rag-retrieval-eval-without-benchmark`); more questions of the same kind narrow the interval around a biased number.
- **Evidence strength:** common practice (statistics of evals: an Anthropic research paper plus independent follow-ups; IR topic counts: several peer-reviewed IR papers over 25 years; latency percentiles: vendor and practitioner sources only).
- **Sources:**
  - Miller, "Adding Error Bars to Evals", arXiv 2411.00640 (research paper, Anthropic): https://arxiv.org/pdf/2411.00640
  - Bowyer, Aitchison and Ivanova, "Position: Don't use the CLT in LLM evals with fewer than a few hundred datapoints", arXiv 2503.01747 (research paper): https://arxiv.org/pdf/2503.01747
  - Voorhees, "Evaluation: how well does system..." (CLEF workshop slides, NIST): https://www.ercim.eu/publication/ws-proceedings/CLEF2/vorhees.pdf
  - Sanderson, IR evaluation (author's paper, discusses topic counts): https://marksanderson.org/files/papers/IR2019.pdf
  - Sample-size design for IR test collections (Springer, Information Retrieval Journal): https://link.springer.com/content/pdf/10.1007/s10791-016-9281-7.pdf
  - Last9, "Your percentiles are incorrect P99 of the times" (vendor blog): https://last9.io/blog/your-percentiles-are-incorrect-p99-of-the-times/
  - Loadster, response time percentiles (vendor FAQ): https://loadster.com/faqs/response-time-percentiles/
  - Baeldung, p99 latency (tutorial): https://www.baeldung.com/cs/whats-the-p99-latency
- **Limits:** Read through search summaries; the papers were not read in full. The Buckley and Voorhees year is given as 2000 in most sources and 2002 in one NIST listing. No authoritative count exists for latency percentiles; the 100 / 1,000 figures are a minimum for the percentile to exist, from vendor sources. The per-n half-widths are the checker's own arithmetic.
- **Checked:** 2026-11-15
