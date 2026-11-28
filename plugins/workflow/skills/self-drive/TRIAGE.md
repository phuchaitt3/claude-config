# Resume triage: label a repository's issues for the ranking

(User's decision, 2026-11-15.) One pass per repository, run before an overnight run (overnight mode, "Before the first round") or whenever the user asks a chat to "triage resume relevance for <repo>". It labels open issues so `next_task.py` can rank resume work first; the script then only reads labels, so the order stays fixed and repeatable from round to round.

**The gap list** is `~/.claude/resume-gaps.md`, or, when that file's first line is `source: <absolute path>`, the file it names (so the list can live in a private repository that both machines sync; this repository is public and names no path to it). Paths written inside the list are relative to the root of the repository that holds it. Below, "the gap list" means that content.

Skip the pass when `~/.claude/resume-gaps.md` (or the file it points to) does not exist or the project's `CLAUDE.md` says "no gap list".

## Who runs it

One worker subagent, Opus at medium effort (`model: "opus"`, `effort: "medium"`; `workflow:subagents` applies). Opus because each label maps an issue to specific resume bullets across two documents, and a wrong label steers every round of the night; the run itself stays on Sonnet. Issues the run files later are labelled by the loop chat when it files them (user's decision, 2026-11-15). The loop chat passes the repository and this file's path, and reads back only the report.

## Inputs (read, never copy into the repository)

- The gap list: the ranked skill groups (slug in backticks), which target names each, the resume file for each target, and which groups are must-haves for which target.
- The resume files it names. Bullets are LaTeX macros in the master content file (`content.tex` beside `master.tex`); a target variant cuts a bullet by redefining its macro as empty, so a bullet is on the target-1 resume when the variant does not empty it. Only bullets of the entry for this repository's project count for `resume:1` to `resume:3` (match the entry by project name or repository link; a project spread over two repositories shares one entry).
- The open issues of this repository (`gh issue list --state open --limit 200 --json number,title,body,labels`).
- Leave `saved-run` issues unlabelled: they are queued runs, not tasks (`SKILL.md`, "Saved runs").
- Skip issues already carrying a `resume:` or `resume:none` label (the incremental pass, run before every overnight run) unless a full re-triage is due. **Full re-triage** (relabel issues that already carry a label; user's decision, 2026-11-18) runs when `~/.claude/resume-gaps.md` changes, when the user asks, or when `picks_log.py report` shows the loop passing over the top-ranked issue repeatedly for a reason a label would fix; otherwise at most once every 2 weeks, and not before 7 nights of picks are logged. The gap list itself is reviewed monthly or when a new target is added, never because of the pick log alone (standard: findings/priority-review-cadence, checked 2026-11-18; the thresholds are inference).

## Labels

Create any label that is missing (`gh label create <name> --description <text> --force`). Descriptions name skill groups and kinds only.

| Label | Meaning |
|---|---|
| `resume:1` | Gives a weak bullet of this repository's project, as it appears on the target-1 resume, a measured number or data, so it becomes strong (weak: no number, or no baseline). |
| `resume:2` | Makes another bullet of this project on the target-1 resume stronger (deeper result, sharper baseline, a defensible detail an interviewer will ask about). |
| `resume:3` | Makes a bullet of this project that is in the master resume but cut from the target-1 resume stronger (weak ones first when choosing among several). |
| `resume:4` | Gives evidence for a target-2 must-have group the resume does not yet show. |
| `resume:5` | Any other gap-list group: backs a bullet's existing claim with other tools or documentation, or fills a nice-to-have. |
| `resume:6` | A new claim not yet on any resume, in a gap-list group. |
| `resume:none` | Serves no gap-list group (so the next pass skips it). |
| `heavy` | Optional hint, not part of this pass: triage or a human may set it when a finish plainly needs the laptop (a full test suite, a local GPU job or large model or dataset load, or a Compose stack). Work that runs on Kaggle is not `heavy`. Do not label every issue for it; the loop adds it from evidence (a low-memory kill or a long lock wait; SKILL.md, "Heavy-task hold"; standard: findings/heavy-task-tagging, checked 2026-11-18). |
| `gap:<slug>` | The gap-list group it serves (slug from `resume-gaps.md`); one per issue, the best-ranked when several fit. |

An issue gets the lowest-numbered `resume:` label that is true for it. Pick a kind only when the issue's finish would actually let a bullet say something new; an issue that touches a group's topic but changes no claim is `resume:none`.

'Stronger' in `resume:1` to `resume:3` means the bullet's claim itself changes: a new number or baseline, a deeper result, or a detail an interviewer will probe. Changing only the tools or precision behind the same claim, or documenting a claim already made, is `resume:5` when it fills a gap-list nice-to-have, and `resume:none` otherwise (user's decision, 2026-11-18, after a rerun that only swapped tools was read as both `resume:2` and `resume:5`).

## For each labelled issue

Add one comment: `Resume triage: resume:<k>, gap:<slug>. <one line why, naming the skill group, never a company, posting or resume text>.` signed with the session ID. The repository may be public, so no employer name, posting name, resume wording or personal detail goes into a label, a comment or a commit.

## Review by the user (user's decision, 2026-11-18)

The user does not review the labels by hand: a wrong label costs one night's pick and one command to undo, and the mechanical gaps (a missing dependency link, an owner review without `needs-you`) are printed as `fix:` lines by `next_task.py`. Before a night that matters, the user reads the top ten of its output and the `fix:` lines; the cadence of a full re-triage is in "Inputs" above (standard: findings/priority-review-cadence, checked 2026-11-18).

## Report (at most 10 lines)

Counts per label, the issue numbers labelled `resume:1` to `resume:4`, and any group from the gap list that no open issue serves (the overnight run may file issues for those, "New issues").
