---
topic: clicklock-mouse-without-borders
area: Software process
question: Do other users report that Windows ClickLock needs two clicks to end a selection when the mouse is shared through PowerToys Mouse Without Borders, and is there a known fix?
checked: 2026-11-23
review_months: 6
status: current
---

# ClickLock with Mouse Without Borders

- **Question:** With ClickLock on, a user holds the button to select, and ending the selection takes two clicks (one before Mouse Without Borders was in use). Do others report it, and is there a fix?
- **Finding:** No report of this exact combination was found: no GitHub issue, forum thread or blog ties ClickLock to Mouse Without Borders. Two searches (standard and extended) on 2026-11-23 returned only neighbouring complaints: clicks that stop working after the link connects (Microsoft Q&A), and a 2014 comment that Mouse Without Borders makes clicks count as double clicks, "drag n' drops, selections quite painful", with no fix given (gHacks comment). No PowerToys issue about ClickLock was found.
- **How ClickLock works (official-style guides):** hold the primary button briefly, move to select or drag, then click again to release. The Windows setting lives in Mouse properties, Buttons tab; it is a per-machine Windows setting.
- **Inference (not a source):** ClickLock acts where the click is received. With Mouse Without Borders the physical mouse is read on one machine and the clicks are replayed on the other, so the hold time or the release may be seen differently on each side. That would explain the extra click, but nothing found confirms it. Which machine has ClickLock on, and whether turning it off on the receiving machine (or both) removes the symptom, is untested.
- **Evidence strength:** *no data found* for the combination; *anecdotal* for the neighbouring symptoms.
- **Sources:**
  - [Mouse without borders connects for 2 clicks only](https://learn.microsoft.com/en-us/answers/questions/4091861/mouse-without-borders-connects-for-2-clicks-only) (Microsoft Q&A; generic replies, no resolution seen; snippet only)
  - [Fixing Mouse without Borders annoyances](https://www.ghacks.net/2012/07/16/fixing-mouse-without-borders-annoyances/) (gHacks, 2012 article; double-click comment from 2014; snippet only)
  - [Mouse Without Borders docs](https://learn.microsoft.com/en-us/windows/powertoys/mouse-without-borders) (Microsoft docs; no mention of ClickLock)
  - [How to drag without holding the button](https://www.howtogeek.com/212342/how-to-highlight-and-drag-and-drop-without-holding-the-mouse-button-down-in-windows/) (How-To Geek; ClickLock behaviour)
  - [PowerToys issue 26537](https://github.com/microsoft/PowerToys/issues/26537) (symptom not read; not confirmed related)
- **Limits:** pages were read as search summaries; GitHub's own search was not run, so an issue titled "click lock" or "sticky drag" could exist. Reddit was not searched.
- **Checked:** 2026-11-23
