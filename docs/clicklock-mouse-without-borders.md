# ClickLock and Mouse Without Borders (open issue)

Written 2026-11-23 so the problem need not be rediscovered.

**Intended state:** ClickLock off (Settings > Bluetooth & devices > Mouse > Additional mouse settings > Buttons tab > "Turn on ClickLock"), on both machines, while PowerToys Mouse Without Borders shares one mouse and keyboard between the laptop and the PC.

**Symptom:** with ClickLock on, holding the button to select ends the selection only after two clicks; before Mouse Without Borders it took one.

**What is known:** an external check found no report of this combination and no fix (`findings/clicklock-mouse-without-borders.md`, checked 2026-11-23, re-check by 2027-05-23). Cause untested; the likely idea is that the two machines see the hold and the release differently.

**To turn ClickLock back on, fix this first. Test plan (about 10 minutes):**

1. Note the ClickLock state on both machines (Buttons tab, "Settings" shows the hold time).
2. On the machine that receives the clicks, ClickLock on, other machine off. Drag-select text. Count clicks to end the selection.
3. Swap: on for the machine that owns the physical mouse only, off on the receiver. Repeat.
4. Both on. Repeat. Also try a longer hold time (Settings button next to ClickLock).
5. Record which combination ends a selection in one click. If one does, that is the fix: keep ClickLock only on that machine.
6. If none does, search the microsoft/PowerToys GitHub issues for "click lock" and "sticky drag"; if nothing exists, open an issue with steps 2 to 4 and the PowerToys version.

Update this file and the finding with the result.
