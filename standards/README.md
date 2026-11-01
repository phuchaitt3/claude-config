# Industry-standard register

What agents checked against industry practice, kept so the next chat answers from it instead of searching the web again. Rule: `rules/working-rules.md`, "Industry practice".

The repository is public: an entry names no project and holds no private detail.

## How to use it

- Before a web search about an industry practice, look for the topic below. If an entry covers the question and is under 12 months old, answer from it and cite it as `standards/<topic>`.
- After a search that checks a practice, add or update the entry in the same turn, and tag the point where it is written: `(standard: standards/<topic>, checked YYYY-MM-DD)`, or `(departs from standard: <reason>)`.
- An entry older than 12 months, a source that has changed, or a new fact that contradicts it means check again and update the entry.

## Entry format

One file per topic, `standards/<topic>.md`:

- **Question:** what was asked, in one line.
- **Finding:** the answer in a few lines, as the sources say it. Mark what is the checker's own inference.
- **Sources:** links, each with its kind (official docs, standard body, vendor blog, community post).
- **Limits:** what the sources do not cover, and any source that is secondary or low quality.
- **Checked:** date.

## Index

| Topic | Question |
|---|---|
| [code-owners-required-review](code-owners-required-review.md) | How does GitHub enforce a list of paths that only the owner may merge? |
| [policy-single-source](policy-single-source.md) | How do rules in prose and in enforcement code stay in step? |
| [agent-config-protection](agent-config-protection.md) | How are an AI agent's own config files (instructions, settings, hooks) protected from automated changes? |
| [secret-leak-prevention](secret-leak-prevention.md) | How is a secret kept out of a public repository, and how common are leaks? |
| [leaked-secret-response](leaked-secret-response.md) | What to do first when a secret has been pushed. |
| [heavy-job-scheduling](heavy-job-scheduling.md) | How do teams run heavy tests and benchmarks without slowing people, and what scheduling tools exist for an agent on a laptop? |
