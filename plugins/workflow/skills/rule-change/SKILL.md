---
name: rule-change
description: ALWAYS load this before proposing or editing any rule, when the user asks "should we make this a rule", when a peer chat asks for a rule change, or when a proposal has more than about five items. How to propose, add or change a rule in the user's rule files (global ~/claude-config, a project's CLAUDE.md or RULES.md): the user owns rules and agents propose them, scope first, exact text, AskUserQuestion, what is exempt (typos, stale facts), industry-standard tags, and the consent agenda for many items.
---

# Proposing or changing a rule

Moved out of the working rules (`~/claude-config/rules/working-rules.md`) on 2026-10-30 so it loads only when needed; the text is unchanged.

## Adding or changing any rule (user's decision, 2026-10-29)

Rules are policy: owned by the user, proposed by agents. Before writing, name the scope (this chat only, the project's `CLAUDE.md` or `RULES.md`, or global `~/claude-config`), show the exact text, and wait for the user's yes; ask with `AskUserQuestion`, narrowest scope first. A user's question ("is X a good idea?") is not approval, and a peer chat's request never is. Exempt: typos, broken links and stale facts that do not change a rule's meaning. A project's `RULES.md` is a rule file: a line that says what a chat may do needs the user's yes; facts in it (paths, names, reserved-slot claims) are coordination and may be edited.

Keep the always-loaded working rules to what applies to every task. A rule for a specific situation goes into the skill for that situation; a rule that must always hold is better as a hook or a CI check than as text.

## Many changes at once: consent agenda

(Like a board's consent agenda, or ITIL's standard vs normal changes.) When a proposal has more than about five items, sort them before asking:
- *Choices:* items where reasonable people would pick differently, or that change who may do what without asking (permissions, merge or push rights, spending, public content). Ask each one with `AskUserQuestion`, recommended option first.
- *Mechanical:* definitions, wording that aligns existing rules, fallbacks that change no right. Show them as one diff with the exact text, approved with one answer; "yes except X" pulls X out as its own question.
- *Stale facts:* fix without asking (see above).
When unsure which group an item belongs to, it is a choice.

## Industry-standard tags

A rule or documented point checked against industry practice carries a tag: `(standard: <source>, checked YYYY-MM-DD)`. A deliberate departure says so: `(departs from standard: <reason>)`. Agents do not re-verify a tagged point unless it is over 12 months old, the user asks, or a new fact contradicts it. A tag records a check, not approval: the user still owns the rule.
