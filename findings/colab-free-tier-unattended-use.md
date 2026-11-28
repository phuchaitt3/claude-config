---
topic: colab-free-tier-unattended-use
area: ML systems
question: Can free-tier Google Colab be used as an unattended GPU job runner from a terminal or script?
checked: 2026-11-28
review_months: 6
status: current
---
# Free Colab as an unattended job runner

**Question:** Can free-tier Google Colab be used as an unattended GPU job runner from a terminal or script?

**Finding:**
- The FAQ lists, as disallowed on free runtimes without a compute-unit balance, "remote control such as SSH shells, remote desktops" and "bypassing the notebook UI to interact primarily via a web UI"; such runtimes may be terminated without warning.
- Free runtimes run "at most 12 hours, depending on availability and your usage patterns"; GPU access is "heavily restricted", idle runtimes time out, and limits are not published.
- An official CLI exists (`googlecolab/google-colab-cli`, Apache-2.0) with a `--gpu` option. Its README says Linux and macOS only, not Windows. It does not say whether free accounts may use it.

**Practice here:** do not build an unattended free-tier Colab runner on the assumption that it is allowed or reliable. Treat Colab as an interactive, by-hand fallback unless Google's pages say otherwise.

**Sources:**
- https://research.google.com/colaboratory/faq.html
- https://github.com/googlecolab/google-colab-cli

**Evidence strength:** official FAQ and README, read once through a fetch summariser. How the FAQ's ban applies to Google's own CLI is not stated anywhere read; the repository's `docs/` files were not read.
