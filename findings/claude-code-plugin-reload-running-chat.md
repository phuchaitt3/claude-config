---
topic: claude-code-plugin-reload-running-chat
area: Agent setup
question: Does a running Claude Code chat pick up a changed plugin skill, does `/reload-plugins` change that, and can an agent trigger a reload in another chat (no)?
checked: 2026-11-15
review_months: 6
status: current
---
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

- **Checked:** 2026-11-14; agent-triggered reload section 2026-11-15

## Can an agent reload another chat's plugins? (checked 2026-11-15)

- **Question:** can an agent, a hook or a script make a running chat (above all a background `claude --bg` loop) reload its plugins, without the user typing `/reload-plugins` in it?
- **Finding: no supported way exists.** `/reload-plugins` is a REPL command a user types. No CLI subcommand, signal, SDK call or hook output triggers it, and a cross-session message that says `/reload-plugins` arrives as plain text, not as a command (seen 2026-11-15: the user could reload only their own chat). The changelog up to 2.1.325 lists reload fixes for mods in `.claude/skills` and for MCP servers, nothing for reloading another session.
- **Requests exist, none shipped.** Four feature requests ask for exactly this: invoke `/reload-plugins` from slash commands or hooks ([#32827](https://github.com/anthropics/claude-code/issues/32827)), a SIGHUP handler for headless sessions ([#36847](https://github.com/anthropics/claude-code/issues/36847)), hot-reload for running background sessions ([#64411](https://github.com/anthropics/claude-code/issues/64411)), and agent-invokable slash commands with `/reload-plugins` as the example ([#46524](https://github.com/anthropics/claude-code/issues/46524)). All four are closed as "not planned", but by the inactivity bot ("Closing for now — inactive for too long"), not by a maintainer decision, so the door is not shut. An open one asks to apply plugin updates automatically in a session with no user turns yet ([#93657](https://github.com/anthropics/claude-code/issues/93657)). A reload's own gaps were reported too: hook script bodies not refreshed ([#53941](https://github.com/anthropics/claude-code/issues/53941), closed as completed) and hooks under `CLAUDE_PLUGIN_ROOT` needing a restart ([#35406](https://github.com/anthropics/claude-code/issues/35406), duplicate).
- **What works instead, for automation:**
  1. **Restart by handover.** End the loop chat and start a successor (`claude --bg`), which loads the current plugin. Self-drive step 7a already does this at the context threshold; a plugin change can trigger the same handover.
  2. **Send the rule as text.** A cross-session message telling the chat to read the changed `SKILL.md` with the Read tool gets new rule text into it at once (done 2026-11-15); the Skill tool would still return the old copy until a reload.
  3. **Change code, not registration (tested 2026-11-15, this setup).** A hook command such as `python "${CLAUDE_PLUGIN_ROOT}/hooks/x.py"` starts a new process each call, and here `CLAUDE_PLUGIN_ROOT` names the plugin's source folder (`C:/Users/LEGION/claude-config/plugins/workflow`), not the versioned cache copy. Test: a probe line, added for about one minute to an existing hook script (`gpu_guard.py`, run before each Bash or PowerShell call) and then reverted, logged its path and `CLAUDE_PLUGIN_ROOT`. 14 runs appeared, 6 of them within seconds of the edit and before the test call, so chats that had loaded the plugin earlier (the two overnight loops were not reloaded) ran the edited file at their next tool call, with no reload. A new entry in `hooks.json` was not tested and still needs a reload, as does a changed skill text. A single registered dispatcher hook that loads check modules from disk would therefore make new checks reach running chats without any reload. Caveats: a bad edit breaks that hook in every running chat at once, so such files want a test and an atomic write; and it holds only while the plugin is installed from a folder (a marketplace install from a versioned cache would differ).
- **Evidence strength:** *documentary* for "no supported way" (changelog, issue tracker, read 2026-11-15) and *anecdotal* for the text-message route and the edit-takes-effect test (one machine, one probe, one Claude Code build; the chat that ran each logged line was not identified, so "chats not reloaded ran it" rests on timing).
- **Limits:** the changelog fetch covered only the newest entries (2.1.318 to 2.1.325) in full; the issue search may miss a request filed under other words. Re-check when a new Claude Code release mentions reload or headless sessions.

## Loop prompt test (2026-11-14, same chat, after the reload above)

- **Setup:** a `ScheduleWakeup` call with a prompt carrying a unique token (`LOOPTEST-7f3a`) and the instruction not to invoke any skill.
- **Result 1, the prompt returns verbatim:** the wakeup arrived about 117 seconds after a request for 60 (the harness clamped the delay up), as a user turn whose text was exactly the stored string, token included.
- **Result 2, no new skill text arrives with a wakeup:** the wakeup carried only the stored prompt. Nothing was re-read or re-expanded, and no Skill call was made in that turn, so the chat's view of the skill did not change. The chat sees the reloaded skill text only when it calls the Skill tool again (the first test above).
- **Consequence:** a loop chat whose stored brief is the old text keeps acting on it, because the brief is a string held in the chat's own context and re-sent as is. Reloading plugins does not rewrite it. A running overnight loop gets new rules by ending the chat and starting a new one.
- **Limits:** one wakeup, in an ordinary chat that was not running a real `/loop` skill; the harness's own loop bookkeeping could differ and was not inspected. The test shows the prompt is verbatim; that a real brief also stays stale follows from that, but a long-running loop chat was not tried.
