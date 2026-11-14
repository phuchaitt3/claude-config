# Does a running Claude Code chat pick up a changed plugin skill?

- **Question:** After a plugin skill is edited, its version bumped and the installed copy updated, does a chat that is already running get the new skill text? Does `/reload-plugins` change that? What about a loop that keeps re-sending an older copy of the skill's text as its prompt?

- **Finding (tested in one chat, 2026-11-14, Claude Code in the VS Code extension on Windows):**
  - **Before a reload, no.** The plugin on disk was already at the new version (`claude.exe plugin update` had said "Restart to apply changes"). In a chat that had loaded the skill earlier, calling the Skill tool for the same skill returned only "already loaded above; instructions unchanged", not the new text. A chat therefore keeps the copy it first loaded.
  - **After `/reload-plugins`, yes, on the next load.** The user typed `/reload-plugins` in that chat (output: plugin "re-read from its folder", 1 plugin, 14 skills, 38 hooks). Calling the Skill tool again then returned the new text, with the changes made after the first load present. A new session loads the new text without any reload.
  - **A loop prompt keeps its stored text (tested, see "Loop prompt test" below).** A self-paced loop passes a brief as the `ScheduleWakeup` prompt, and the wakeup re-sends that string. A reload changes what the Skill tool returns on a new call, not a prompt string already stored in a running loop. The safe route for a running loop is to end the chat and start a new one, which loads the current skill text and sets a new loop prompt.
  - **The hook text and files follow the same re-read** (the reload output counts hooks), but only the skill text was checked.

- **Evidence strength:** *anecdotal* (one chat, one machine, one reload; the harness messages quoted above are the evidence). The official plugin docs were not consulted for this entry.

- **Sources:** none outside the test; the behaviour is the tool's own and can change between versions.

- **Limits:** One test, on one Claude Code build and one platform. It did not check hooks, whether a loop's stored prompt can be refreshed, or whether the Skill tool's "already loaded" notice appears for every skill. A chat that never calls the Skill tool again reads nothing new, reload or not.

- **Checked:** 2026-11-14

## Loop prompt test (2026-11-14, same chat, after the reload above)

- **Setup:** a `ScheduleWakeup` call with a prompt carrying a unique token (`LOOPTEST-7f3a`) and the instruction not to invoke any skill.
- **Result 1, the prompt returns verbatim:** the wakeup arrived about 117 seconds after a request for 60 (the harness clamped the delay up), as a user turn whose text was exactly the stored string, token included.
- **Result 2, no new skill text arrives with a wakeup:** the wakeup carried only the stored prompt. Nothing was re-read or re-expanded, and no Skill call was made in that turn, so the chat's view of the skill did not change. The chat sees the reloaded skill text only when it calls the Skill tool again (the first test above).
- **Consequence:** a loop chat whose stored brief is the old text keeps acting on it, because the brief is a string held in the chat's own context and re-sent as is. Reloading plugins does not rewrite it. A running overnight loop gets new rules by ending the chat and starting a new one.
- **Limits:** one wakeup, in an ordinary chat that was not running a real `/loop` skill; the harness's own loop bookkeeping could differ and was not inspected. The test shows the prompt is verbatim; that a real brief also stays stale follows from that, but a long-running loop chat was not tried.
