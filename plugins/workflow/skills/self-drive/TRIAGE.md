# Resume triage: label a repository's issues for the ranking

(User's decision, 2026-11-15.) One pass per repository, run before an overnight run (overnight mode, "Before the first round") or whenever the user asks a chat to "triage resume relevance for <repo>". It labels open issues so `next_task.py` can rank resume work first; the script then only reads labels, so the order stays fixed and repeatable from round to round.

Skip the pass when `~/.claude/resume-gaps.md` does not exist or the project's `CLAUDE.md` says "no gap list".

## Who runs it

One worker subagent (Sonnet, medium effort; `workflow:subagents` applies). The loop chat passes the repository and this file's path, and reads back only the report.

## Inputs (read, never copy into the repository)

- `~/.claude/resume-gaps.md`: the ranked skill groups (slug in backticks), which target names each, the resume file for each target, and which groups are must-haves for which target.
- The resume files it names, and the open issues of this repository (`gh issue list --state open --limit 200 --json number,title,body,labels`).
- Skip issues already carrying a `resume:` or `resume:none` label, unless the user asked for a full re-triage.

## Labels

Create any label that is missing (`gh label create <name> --description <text> --force`). Descriptions name skill groups and kinds only.

| Label | Meaning |
|---|---|
| `resume:1` | Gives a weak bullet on the target-1 resume a measured number or data, so it becomes strong (weak: no number, or no baseline). |
| `resume:2` | Makes another target-1 resume bullet stronger (deeper result, sharper baseline, a defensible detail an interviewer will ask about). |
| `resume:3` | Gives evidence for a target-2 must-have group the resume does not yet show. |
| `resume:4` | Any other gap-list group: strengthens a bullet or fills a nice-to-have. |
| `resume:5` | A new claim not yet on any resume, in a gap-list group. |
| `resume:none` | Serves no gap-list group (so the next pass skips it). |
| `gap:<slug>` | The gap-list group it serves (slug from `resume-gaps.md`); one per issue, the best-ranked when several fit. |

An issue gets the lowest-numbered `resume:` label that is true for it. Pick a kind only when the issue's finish would actually let a bullet say something new; an issue that touches a group's topic but changes no claim is `resume:none`.

## For each labelled issue

Add one comment: `Resume triage: resume:<k>, gap:<slug>. <one line why, naming the skill group, never a company, posting or resume text>.` signed with the session ID. The repository may be public, so no employer name, posting name, resume wording or personal detail goes into a label, a comment or a commit.

## Report (at most 10 lines)

Counts per label, the issue numbers labelled `resume:1` to `resume:3`, and any group from the gap list that no open issue serves (the overnight run may file issues for those, "New issues").
