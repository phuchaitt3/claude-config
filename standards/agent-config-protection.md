# Protecting an AI agent's own config files

- **Question:** How are an agent's instruction, settings and hook files protected from automated changes?
- **Checked:** 2026-11-01

## Finding

- Agent config (`CLAUDE.md`, `AGENTS.md`, `.claude/settings.json` and hooks, `.mcp.json`) is treated as its own attack surface: an agent that can edit its gate can loosen it.
- Guidance: give these files the same static scanning and pull-request gating as CI pipeline files, and review edits to `AGENTS.md` like CI changes.
- Layer the defences: harness-level blocks (pre-tool hooks) are deterministic, `CODEOWNERS` puts agent accounts under the same restrictions as other contributors, and a CI or merge gate still stops a model that ignores instructions.
- Tools exist that block agent edits to CI files or keep a trusted baseline of agent config; treat their claims as unverified.

## Sources

- [Agent Infrastructure as Code (Cycode)](https://cycode.com/?p=11538) (vendor).
- [Indirect AGENTS.md injection (community write-up)](https://codex.danielvaughan.com/2026/05/01/indirect-agents-md-injection-codex-cli-supply-chain-defence/).
- [AGENTOWNERS thread (r/devops)](https://r.datuan.dev/r/devops/comments/1u9eejb/agentowners_block_ai_agents_from_editing/) (community).

## Limits

No authoritative standard or official guidance found. All sources are vendor or community pages.
