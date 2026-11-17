---
topic: claude-code-multi-repo-sessions
area: Agent setup
question: Should an agent session be started in each repository, or should one session work across several repositories?
checked: 2026-11-17
review_months: 6
status: current
---
# One Claude Code session per repository, or one session across repositories

**Question:** Is it normal to start a separate coding-agent session in each repository, or to work across repositories from one session?

**Finding:**

- Claude Code takes its project settings, `CLAUDE.md` and permission rules from the folder it was started in. Other folders are added with `--add-dir`, `/add-dir` or the `additionalDirectories` setting. Added folders follow the same permission rules as the working directory (quoted from the IAM docs by a GitHub issue).
- An added folder's `CLAUDE.md` is not loaded by default; `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` turns that on for `--add-dir` and `/add-dir`. Folders listed in `additionalDirectories` get file access only, no `CLAUDE.md` or rules. Skills, commands and agents of an added folder load regardless.
- The docs and guides present `--add-dir` for a task that spans repositories (a frontend and its backend, a sibling package). One guide says to start at a monorepo root so no extra folders are needed. Anthropic's large-codebases guidance suggests running exploration in subagents so file reads stay out of the main conversation. One practitioner notes that exploring a second repository in the same session costs context.
- No source compares the two setups or calls either one the standard. Checker's inference, not stated by the sources: a session started in each repository is the default because that is where its rules and settings load, and a session that reaches into a second repository gets that repository's rules only through the opt-in above or by being told them.
- Consequence for a rule that reads one repository's files: it sees only the folder the session started in. A gate that reads `CLAUDE.md` from the session folder does not read the repository named in a `cd` inside a command; it needs the repository named explicitly.

**Evidence strength:** *vendor or single source* for the mechanics (official docs summarised through search results, plus community posts); no evidence on which setup is more popular.

**Sources:**

- Claude Code docs, [large codebases](https://code.claude.com/docs/en/large-codebases.md) (official docs; only the search summary was read, not the full page).
- Claude Code docs, [memory and CLAUDE.md](https://code.claude.com/docs/en/memory) (official docs; summary only).
- [wikidocs: add-dir and CLAUDE.md loading](https://wikidocs.net/345374) (community guide, Korean).
- [claude-code issue 21138](https://claudeissues.com/issue/21138-docs-add-dir-can-load-claude-md-from-additional-directories-new-in-2-1-20-undocu) and [issue 45643](https://github.com/anthropics/claude-code/issues/45643) (community issue reports).
- [apidog](https://www.apidog.com/blog/claude-code-multi-directory-support), [Vincent Qiao](https://blog.vincentqiao.com/en/posts/claude-code-add-dir/), [DEV Community: managing 15 repos](https://dev.to/neil_agentic/how-i-manage-15-repos-with-claude-code-without-losing-my-mind-2ood) (blogs).

**Limits:** two searches, results read as summaries; the official pages were not opened. The environment variable's behaviour comes from one community guide and may have changed. Nothing here measures popularity.

**Checked:** 2026-11-17
