"""Check: remind a chat to read the findings register before writing an unsourced practice claim into a file.

(User's decision, 2026-11-21, global scope; rule: `rules/working-rules.md`, "Industry practice".)
Runs before a Write or Edit whose new text says what tests, interviews, employers or practice do or
do not ask or use ("nothing shows a test asks it", "no source names", "commonly asked") with no
`findings/` citation, `(standard:` tag, "unchecked" or "my judgement" marker in the same text. It adds
one line: read `~/claude-config/findings/README.md`, cite the entry or a job-data row, or label the
claim "my judgement, unchecked". Edits to the register itself are left alone. Reminder only: a hook
cannot tell a checked claim from a remembered one, so it matches wording and never blocks. It cannot
see claims made in chat text, only those written to files.
Why: a page said "no source shows a test asks it" from memory, and the register held a relevant entry.
"""

import re

EVENTS = {"PreToolUse"}
TOOLS = {"Write", "Edit"}
_CLAIM = re.compile(
    r"\b(?:nothing|no (?:source|posting|finding|data|evidence))\b[^.\n]{0,40}"
    r"\b(?:shows?|names?|says?|asks?|mentions?|confirms?)\b"
    r"|\b(?:is|are|commonly|often|usually|always|never|rarely)\s+(?:asked|tested|used)\b"
    r"|\bstandard practice\b|\bindustry (?:standard|practice)\b"
    r"|\b(?:tests?|interviews?|employers?|recruiters?)\s+(?:rarely|never|always|usually|often)\b",
    re.I,
)
_SOURCED = re.compile(r"findings/|\(standard:|departs from standard|unchecked|my judge?ment|mentions\.csv|postings\.csv", re.I)


def run(payload):
    tool_input = payload.get("tool_input") or {}
    path = str(tool_input.get("file_path", "")).replace("\\", "/")
    if "/findings/" in path or "findings-" in path:
        return None
    text = str(tool_input.get("new_string") or tool_input.get("content") or "")
    if not _CLAIM.search(text) or _SOURCED.search(text):
        return None
    return ("unsourced-claim: this text says what tests, employers or practice do or do not ask or use, with no "
            "source. Before writing it, read `~/claude-config/findings/README.md`; if a current entry covers it, "
            "cite it as `(standard: findings/<topic>, checked YYYY-MM-DD)`, or cite the job-search data row. "
            "If nothing covers it, write \"my judgement, unchecked\" (or search the web and add a register entry). "
            "Otherwise ignore this.")
