# Reporting a benchmark result measured on several setups: a range, the best case, or each one?

- **Question:** When one method was measured on several setups (two GPUs, two workloads) with different gains, may a resume or report give a range ("1.8-2.5x"), or should it give only the best one?
- **Finding:**
  - **Reporting only the best is the named flaw.** Heiser's "Systems Benchmarking Crimes" calls selective benchmarking (a biased choice of benchmarks or data sets) the most serious crime: a hand-picked subset is "most likely cherry-picked to look favourable". ML guides list "best of several runs in the main table, the rest in an appendix" as cherry-picking, and advise reporting every configuration or seed with its spread, and disclosing how many runs were made.
  - **Each result names its own setup** (hardware, software, workload): see [benchmark-setup-consistency](benchmark-setup-consistency.md). A range is acceptable when every endpoint is a measured result on a named setup and the scope in which it holds is stated; the setups left out should not be worse cases of the same scope.
  - **Resumes:** career guides say a number is a claim to defend in the interview, and that conditions (hardware, workload) should sit beside it. None found sets a rule for ranges across hardware, and none discusses "up to" phrasing for benchmarks.
  - *Checker's inference:* a range across the setups that were run, with the scope named ("on the thesis workload, on two GPUs"), is honest; the best endpoint alone is not. If worse setups exist outside that scope, the interview answer states them. When the saving is a trade (less memory at about the same speed), the speed result belongs beside it; otherwise the saving reads as free.
- **Sources:**
  - [Heiser, Systems Benchmarking Crimes](https://gernot-heiser.org/benchmarking-crimes.html) (academic checklist; search summary).
  - [Benchmarking Crimes (reading-list PDF)](https://cs.uwaterloo.ca/~brecht/courses/Perf-Eval-Shared/readings/f20/benchmarking-crimes.pdf) (course reading; search summary).
  - [Questionable practices in ML](https://www.gleech.org/files/papers/questionable-practices-ml) (taxonomy paper; search summary).
  - [Benchmarking methodology (theorempath)](https://theorempath.com/topics/benchmarking-methodology) (guide; search summary).
  - [Resume metrics guide (The Career Launchpad)](https://thecareerlaunchpad.beehiiv.com/p/the-deal-with-resume-metrics) (newsletter; weak source).
- **Limits:** Read through search summaries only. No source states a rule for ranges across hardware or "up to" phrasing; the resume part is the checker's inference. Resume sources are blogs; statistics in them have no cited origin and are ignored.
- **Checked:** 2026-11-12
