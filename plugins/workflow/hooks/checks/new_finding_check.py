"""Check: before a NEW findings/<topic>.md is written, list the nearest existing entries.

User's decision, 2026-11-23 (global scope): the register had grown one file per narrow fact (30
resume-* and 10 rag-* files, several answering sub-questions of one topic). Regrouping old entries
periodically was ruled out, so the check works when an agent adds one entry at a time.

Runs before a Write whose target is `findings/<topic>.md` (not README.md) and does not exist yet. It
adds the 3 nearest existing entries (word overlap of topic name and question, across all areas,
plus a bonus for the same first word of the topic) and the rule: add a dated bullet to one of them,
or state in the entry's Question line why this question is separate; a new entry needs at least two
sourced lines or a decision no other entry covers. Reminder only: it never blocks, and an existing
file, an edit or any other path is left alone.
Evidence: findings/knowledge-register-entry-granularity.
"""

import re
from pathlib import Path

EVENTS = {"PreToolUse"}
TOOLS = {"Write"}
BONUS = 0.15
CLUSTER_AT = 3
_STOP = set("a an the of in on for to and or is are be it how what which when do does with by at as from vs should my this that".split())


def _tokens(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP and len(w) > 2}


def _question(text: str) -> str:
    m = re.search(r"^question:\s*(.*)$", text, re.M)
    return m.group(1).strip() if m else ""


def nearest(topic: str, question: str, register: Path, n: int = 3):
    mine = _tokens(topic.replace("-", " ") + " " + question)
    first = topic.split("-")[0]
    scored, same_first = [], 0
    for f in register.glob("*.md"):
        if f.name == "README.md" or f.stem == topic:
            continue
        try:
            q = _question(f.read_text(encoding="utf-8"))
        except OSError:
            continue
        theirs = _tokens(f.stem.replace("-", " ") + " " + q)
        score = len(mine & theirs) / max(1, len(mine | theirs))
        if f.stem.split("-")[0] == first:
            score += BONUS
            same_first += 1
        scored.append((score, f.stem, q))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return scored[:n], same_first


def run(payload):
    ti = payload.get("tool_input") or {}
    path = Path(str(ti.get("file_path", "")))
    if path.suffix != ".md" or path.parent.name != "findings" or path.name == "README.md" or path.exists():
        return None
    near, same_first = nearest(path.stem, _question(str(ti.get("content", ""))), path.parent)
    if not near:
        return None
    lines = [f"new-finding: `{path.name}` is a new register entry. Nearest existing entries:"]
    lines += [f"  - {stem} ({score:.2f}): {q}" for score, stem, q in near]
    lines.append("Add a dated bullet to one of these if the question is the same topic. Otherwise state in the new "
                 "entry's Question line why it is separate. A new entry needs at least two sourced lines, or a "
                 "decision no other entry covers (findings/knowledge-register-entry-granularity).")
    if same_first >= CLUSTER_AT:
        lines.append(f"{same_first} entries already start with `{path.stem.split('-')[0]}-`: prefer appending.")
    return "\n".join(lines)
