---
name: new-project
description: ALWAYS load this at the start of a new project, when a repository has no tier or mode recorded, when configuring git pushes as the bot, or when adding environment settings or a .env file. Covers proposing a tier (solo-fast, standard, strict) and asking the mode (build, study-design), deploys by tier, the user's one-time GitHub setup (bot collaborator, protect-main ruleset, CODEOWNERS, delete-branch-on-merge, push protection), the bot's git push config, and how environment settings and .env files are handled.
---

# New project setup

Moved out of the working rules (`~/claude-config/rules/working-rules.md`) on 2026-10-30 so it loads only when needed; the text is unchanged.

## Project tiers (proposed by the agent, confirmed by the user)

At the start of a new project, propose a tier in one line with the reason; the user confirms once, then record it at the top of the project's `CLAUDE.md`. Never pick or change a tier without that confirmation. A confirmed **solo-fast** tier is the user's standing exception to the Hard limits' "ask before merging a PR"; nothing else in the Hard limits is relaxed by any tier.

| Tier | When | Pull requests |
|---|---|---|
| **solo-fast** | personal project, no users, no money, no private data | agents open PRs freely; any chat other than the author reviews and enables auto-merge (see `workflow:pr-review`); the user merges only PRs touching the paths the project's `CLAUDE.md` lists; default: `CLAUDE.md`, `.github/` (a project may narrow this by risk), infra/deploy, lockfiles, secrets, money, public positioning |
| **standard** (default) | shared repo, collaborators, or anything others depend on | agents push branches; the user opens and merges PRs |
| **strict** | thesis/paper claims, client work, production with users | as standard, plus the user reviews every diff before merge |

**Deploys by tier** (standard: DORA continuous deployment; GitHub environment protection rules; checked 2026-10-29).
- solo-fast: every merge to the default branch may deploy, once spending is capped (budget alert, instance limits); `CLAUDE.md` says so.
- standard: merges deploy to staging; production waits for the user's approval in a GitHub environment with required reviewers.
- strict: as standard, with "prevent self-review" on and admin bypass off.

Hard limits (credentials, force-push, paid jobs over the threshold, publishing) apply in every tier.

## Project mode (asked at project start, chosen by the user; user's decision, 2026-10-30)

At the start of a new project, with the tier, ask which mode it runs in (`AskUserQuestion`, default first) and record it at the top of the project's `CLAUDE.md`. Never pick or change a mode without the user's answer. A project with no recorded mode runs in **build**.

| Mode | Goal | Who decides the architecture |
|---|---|---|
| **build** (default) | ship working software fast | agents, under "Decision rights" |
| **study-design** | the user learns system design through the project | the user; agents brief and implement |

**Details per mode** live in `~/claude-config/modes/<mode>.md`. In one line, **study-design**: an agent does not choose an architecture; it writes a design brief and waits for the user's decision, and the user writes the ADR in their own words. More modes may be added; each says who decides what.

## Why `main` is protected

In project repositories (several chats, collaborators, reviewable history) the usual practice is a protected default branch plus review, so agents work on branches and a human or lead merges. A single-owner config repo has no reviewer, so a branch-and-merge step there adds friction and no safety.

## Agents' GitHub identity (user's decision, 2026-10-29; standard: separate bot identities for automation, as GitHub machine users, Dependabot and Copilot's coding agent use; checked 2026-10-29)

- Agents act on GitHub as the machine user **`phuchai-bot`**, not as the user (`phuchaitt3`). `gh` holds both accounts on each machine, with the bot active. Before any GitHub write, check `gh auth status`. Never run `gh auth switch`, `login` or `logout` yourself: the user manages the accounts. If the bot is missing or inactive, ask the user before writing.
- Pushes go out as the bot too. The global git config pins the user's account (`credential.https://github.com.username phuchaitt3`), so the user's repositories keep their own login. A repository the agents push to overrides that in its own config: `git config credential.https://github.com.helper ""`, then `git config --add credential.https://github.com.helper "!gh auth git-credential"` and `git config credential.https://github.com.username phuchai-bot`; check with `git push --dry-run`. The config repo `~/claude-config` keeps pushing as the user.
- New project: the user adds `phuchai-bot` as a collaborator with **Write**, never Admin, so it cannot change settings or bypass rulesets. Paths the user merges get a `CODEOWNERS` entry for `phuchaitt3`, and the default-branch ruleset requires code-owner review. GitHub then enforces the user-merge list itself.
- New project: the user runs `gh repo edit <owner>/<repo> --delete-branch-on-merge` once (needs admin; the bot cannot), so a merged branch cannot take more pushes (standard: GitHub setting, checked 2026-10-30). Exception: a repository with long-lived branches other than the default.

## One-time steps for the user (user's decision, 2026-10-30)

The user does these once per repository, because they need admin and the bot has Write only. The agent proposes the list at the start of a project and ticks off what is done.

1. Add `phuchai-bot` as a collaborator with **Write**.
2. Create the `protect-main` ruleset: pull request required, required CI checks, no force-push, code-owner review where the project has user-merge paths.
3. Commit a `CODEOWNERS` entry for `phuchaitt3` on each user-merge path.
4. Run `gh repo edit <owner>/<repo> --delete-branch-on-merge`.
5. Public repository: turn on secret-scanning push protection.
6. Record the tier and mode at the top of the project's `CLAUDE.md`.

## Configuration and secrets (user's decision, 2026-10-30; standard: Twelve-Factor App "III. Config" and the dotenv convention, checked 2026-10-30)

- Settings that differ between machines or deploys (URLs, keys, ports) come from environment variables. A `.env` file is the local-development way to supply them, not a requirement: a project without such settings has none.
- When a project has them: commit `.env.example` (every key, dummy values, a one-line comment each) and keep `.env` and `.env.*` out of git (`.gitignore`, with `!.env.example`). CI and production take values from the platform's secret store (GitHub Actions secrets, the host's environment settings), never from a committed file.
- The app loads the file, not the shell: the framework's own loader (Next.js, Docker Compose), `uv run --env-file .env`, `node --env-file=.env`, or a settings library (pydantic-settings). Do not set up terminals or shell profiles to export `.env` on start: every program run from that shell would see the secrets. If a shell needs per-folder variables, use direnv (loads only inside the folder, only after `direnv allow`), never the profile.
- Python virtual environments need no activation under uv (`uv run` uses `.venv`). Leave VS Code's default of activating the selected interpreter in new terminals on; do not add activation to shell profiles.
- Agents never read `.env` (see Hard limits); they read and update `.env.example`.
