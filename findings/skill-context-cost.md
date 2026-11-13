# Skill listings: context cost and how to switch skills off

- **Question:** what do installed skills cost in context at startup, and how are unused ones switched off (claude.ai account skills and Claude Code skills)?
- **Finding:**
  - Skill descriptions load into context at session start; the body loads only when the skill is invoked. The listing is paid on every turn whether or not a skill is used. The combined `description` and `when_to_use` text is cut at 1,536 characters per skill, so the key use case goes first. An invoked skill's body stays in context for later turns; keep `SKILL.md` under 500 lines and move reference text into supporting files. (Claude Code docs.)
  - Claude Code settings: `disable-model-invocation: true` in a skill's frontmatter removes its description from context (the user can still invoke it). `user-invocable: false` only hides it from the `/` menu and does not cut startup cost. `skillOverrides` in settings (`on`, `name-only`, `user-invocable-only`, `off`) hides skills without editing them, but does not apply to plugin skills (use `/plugin`); `disableBundledSkills` turns bundled skills off. `/skill-doctor` (v2.1.252+) reports each skill's context cost and use and flags never-invoked ones; `/doctor` checks unused skills, MCP servers and plugins against their cost.
  - claude.ai: each skill, including Anthropic's built-in ones, has an on/off switch at **Customize > Skills** (claude.ai/customize/skills); a disabled skill is not available to Claude. Skills need "Code execution and file creation" ("Create and edit files") on under Settings > Capabilities; turning that off disables skills as a group. Team and Enterprise owners manage skills under Organization settings > Plugins & skills.
  - Checker's inference: account skills that sync into Claude Code sessions (they show as `anthropic-skills:*`) are plugin-like, so `skillOverrides` probably does not reach them and the claude.ai switch is the lever; not tested.
  - Blogs measure about 30-100 tokens per skill listing; secondary sources, not official.
- **Sources:**
  - [Claude Code, Skills (official docs)](https://code.claude.com/docs/en/skills), read in part: the last 19,000 characters were not read.
  - [Claude Help Center, Using skills in Claude (official docs)](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
  - [anthropics/claude-code issue 14882 (community report, via search result only)](https://github.com/anthropics/claude-code/issues/14882): skills reported as costing more than the frontmatter at startup; not confirmed fixed.
- **Limits:** the menu path differed between a search snippet (Settings > Capabilities) and the fetched help article (Customize > Skills); the fetched article is used, but check the app if it does not match. No official total listing budget was read. Per-skill token figures come from blogs.
- **Checked:** 2026-11-12
