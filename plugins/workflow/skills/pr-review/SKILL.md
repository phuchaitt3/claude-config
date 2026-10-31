---
name: pr-review
description: ALWAYS load this before opening, reviewing or merging a pull request, when enabling auto-merge, or when a PR leaves work undone. How pull requests are handled across the user's projects: author never approves, review from a pool, review depth by risk, auto-merge after a clean review, the solo-fast tier's user-merge paths, posting the review comment, refreshing open PRs after a merge, and tracking deferred work as issues.
---

# Pull requests: open, review, merge

Moved out of the working rules (`~/claude-config/rules/working-rules.md`) on 2026-10-30 so it loads only when needed; the text is unchanged. The project's `CLAUDE.md` may make any of this stricter.

## Merging in a solo-fast project

A confirmed **solo-fast** tier (recorded at the top of the project's `CLAUDE.md`) is the user's standing exception to the Hard limits' "ask before merging a PR"; nothing else in the Hard limits is relaxed by any tier. In solo-fast, agents open PRs freely; any chat other than the author reviews and enables auto-merge; the user merges only PRs touching the paths the project's `CLAUDE.md` lists (default: `CLAUDE.md`, `.github/` (a project may narrow this by risk), infra/deploy, lockfiles, secrets, money, public positioning). In the **standard** tier agents push branches and the user opens and merges PRs; in **strict**, the user also reviews every diff before merge.

solo-fast needs the permission rules `Bash(gh pr create:*)`, `Bash(gh pr comment:*)` and `Bash(gh pr merge:*)` in the project's `.claude/settings.local.json`; the user adds them. An allow rule matches only a command that starts with it, so run these commands plain (`gh pr create --repo … --body-file …`), never chained after `cd … &&` or with `$(…)`; a chained call falls to the auto-mode classifier and is denied.

## Review and merge (standard: see Sources below, checked 2026-10-29)

Sources: GitHub's rules for required approvals and for Copilot-agent PRs, GitHub team review auto-assignment, Google/Chromium OWNERS review, and published guidance on agent approval authority.

- **Author ≠ approver.** This is the one fixed rule everywhere: GitHub does not count an author's own approval, and whoever assigned a Copilot agent cannot approve its PR. A chat never reviews or merges its own PR, and an agent-authored PR that an agent approved counts as unreviewed by anyone independent.
- **General review comes from a pool, not a dedicated reviewer.** This matches GitHub's team auto-assignment (round robin or load balance) and Google's LGTM, which any engineer can give. Chats of the same model with the same `/code-review` recipe gain nothing from a "reviewer" role. What gives a review its value is independence (a fresh context without the author's assumptions), and a dedicated reviewer chat becomes a bottleneck that idles until prompted. Chats serve the pool by named assignment: the author picks one reviewer, idle first (see the `workflow:multi-chat` skill).
- **Specialize by risk, not by agent.** Industry practice puts named owners on risky paths (CODEOWNERS, Google OWNERS and readability). Here the user is that owner: risky paths (`.github/` risk items, `infra/`, auth, secrets, lockfiles, money, public content) get a deeper review (`/security-review` or `/code-review high`), and the user merges them. Everything else gets `/code-review medium`.
- **Merge authority follows the gate, not the person.** On GitHub anyone with write access may merge once the ruleset is satisfied. So the reviewer does not merge by hand: when the review finds no blocking issue and the PR is not a user-merge item, it runs `gh pr merge <n> --auto --squash`, and GitHub merges when the required checks pass. Restricting merges to the lead adds no safety when every chat is the same model under the same account; it only adds a queue.
- **A blocking issue** is any of: a correctness or security finding the reviewer confirmed, a failing or pending required check, a secret, private identifier or local path in the diff, a touched user-merge path, or an earlier finding not addressed.
- **All chats act as one GitHub account** (the bot, `phuchai-bot`), so GitHub cannot tell author from reviewer, and a required-approvals count cannot enforce author ≠ approver. The inbox rule enforces it. The hard gates are required CI checks and the user-merge list.
- **For anything the user must merge**, request their review (`gh pr edit <n> --add-reviewer phuchaitt3`) and add the `needs-you` label with a comment saying in plain words what it changes, that checks and review are done, and which button to press. The bot cannot approve its own PRs, so agent reviews are comments.
- **Fallback:** an unclaimed PR goes to the lead, except a PR the lead wrote. That one goes to the user, never to its author.
- **After a merge, refresh open pull requests:** the chat that merges, or that first sees a merge, runs `gh pr list --state open --json number,mergeable` and merges the default branch into each of its own pull requests that now conflicts (no rebase, no force-push), in the same session. A conflict in another chat's pull request goes to that chat through the inbox. A pull request waiting on review fixes is its author's first task, so it does not sit open for days (user's decision, 2026-10-30; standard: trunk-based development, short-lived branches).
- **Invest in checks over review.** Studies find agent-only review catches less than human review, and review attention fades with habit. Tests, typing, evaluation jobs and merge queues do not fade, so each one added is worth more than another review pass.
- **GitHub comments are for the record a human reads** (user's decision, 2026-10-30): review verdicts and needs-you notes. A message for another chat goes through SendMessage or the inbox, never a GitHub comment, because GitHub emails the owner and agents do not read notifications.
- **Post the review** as a PR comment (`gh pr comment <n> --body-file …`) stating the verdict, what was checked, findings dropped after checking, and for a `.github/` change, that no user-merge item is touched. If the comment is denied, save the text in the handoff folder, link it in the Review queue row, and continue.

## Deferred work

Before a PR merges, every deferred item (its "Not done" list, and each review finding not fixed in the PR) is an open GitHub issue, or a checklist line in one, and the PR or review comment links it; no bare TODO in code without an issue number (user's decision, 2026-10-30; practice: deferred work gets a tracking issue, review findings are fixed or tracked, checked 2026-10-30). In a public repository an issue never holds private content: that stays in a local ticket and the issue says only "private item; ask in chat".

Workflow work is never low priority (user's decision, 2026-10-31): a change to how agents work (rules, skills, `CLAUDE.md`, process docs, issue and PR templates, hooks) affects every chat from then on. A PR that changes a process updates every file that describes it in the same PR; if one is a user-merge path, the author opens a companion PR for it in the same turn, labelled `needs-you` with the user as reviewer, and links the two. Workflow drift found at any other time is fixed in the turn it is found, or opened at once as a `needs-you` PR if only the user can merge it; never queued as `priority:later` (standard: Google docguide "Update docs with code", checked 2026-10-31).

## Before pushing to an existing branch

Check its PR is still open (`gh pr view <n> --json state`). A merge takes only what was on the branch at that moment, so a later push is lost; after a merge, a follow-up goes on a new branch off the default branch. The `push_guard` hook enforces this.
