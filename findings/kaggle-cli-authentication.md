---
topic: kaggle-cli-authentication
area: ML systems
question: How can the Kaggle CLI authenticate, and does creating a new API token revoke older ones?
checked: 2026-11-27
review_months: 6
status: current
---
# Authenticating the Kaggle CLI

**Question:** How can the Kaggle CLI authenticate, and does creating a new API token revoke older ones?

**Finding:**
- The official CLI docs list four methods: `kaggle auth login` (OAuth in a browser), the `KAGGLE_API_TOKEN` environment variable, a token file at `~/.kaggle/access_token`, and the legacy `~/.kaggle/kaggle.json`.
- Tokens come from the account's API settings page ("Generate New Token"); the legacy file comes from "Create Legacy API Key".
- The docs do **not** say whether an account can hold several tokens, or whether a new token or legacy key expires older ones.
- The docs do not mention `kaggle auth login --force`. The CLI itself (2.2.5, observed once) suggests it when it reports an existing login, even while other commands answer "Authentication required".

**Practice here:** use one token per machine where the settings page allows it, so one can be revoked alone; after creating one, check the other machine still authenticates, because revocation behaviour is undocumented.

**Sources:**
- https://raw.githubusercontent.com/Kaggle/kaggle-cli/main/docs/README.md

**Evidence strength:** official docs for the methods, read once through a fetch summariser; one-token-per-machine is common credential practice, not a statement from Kaggle.
