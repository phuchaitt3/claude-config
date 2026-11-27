---
name: gpu-cap
description: Load when the user asks to cap, throttle or cool the laptop GPU, wants a quieter or cooler laptop for a heavy job, asks to lift or remove the GPU clock cap, or asks whether the cap is on; also before a job that times this laptop's speed. How to switch the GPU clock cap on, off or read its state with one command.
---

# GPU clock cap (laptop only)

Laptop only: the PC has no cap tasks (`setup-machine.ps1 -ClockCap auto` skips them on a desktop), so `cap` does nothing there.

Added 2026-11-18 (user's request, claude-config issue #22). Locks the laptop GPU at 1000-1350 MHz: about 10 °C cooler, 45% less power and about 15% slower than uncapped (20-minute test, 2026-11-17). The tasks behind it are registered by `setup-machine.ps1`; the overnight rule is in `workflow:self-drive` ("GPU clock cap").

**Commands** (one call each; prints ON or OFF, exit 1 if it did not take effect):

- `python ~/claude-config/scripts/gpu_run.py cap on` — cooler and quieter, slower.
- `python ~/claude-config/scripts/gpu_run.py cap off` — full speed.
- `python ~/claude-config/scripts/gpu_run.py cap status` — which one it is now.

**Lenovo mode** (user's decision, 2026-11-27): an agent may start Lenovo Legion Toolkit when a task needs to read or set the Lenovo power mode (`llt.exe feature get|set power-mode`), and may use `scripts/night.ps1` / `game.ps1` for that task. It puts the previous settings back afterwards and says so in its reply. The toolkit needs administrator rights: started from an agent shell that has `__COMPAT_LAYER=RunAsInvoker`, it runs without them and says "This device is not compatible" (found 2026-11-27). So use a toolkit the user already has running, or ask the user to start it.

**When to use which**

- The user says "cool it down", "quiet mode", "cap the GPU": `cap on`. "Full speed", "lift the cap", "I am going to game": `cap off`. "Is the cap on?": `cap status`.
- **Overnight the cap stays on for the whole run, 1350 MHz, project timing benchmarks included** (user's decision, 2026-11-19: a slightly slower timing is better than a hot laptop; "cap off before timing" was meant for the user's own thermal tests). A chat never lifts it for its own jobs. It goes off only for a test of the laptop itself (the cooling reference in `laptop_health.py`, `gpu_cap_bench.py`) run by the user or at the user's request, and goes back on after. A project benchmark report says "GPU capped at 1350 MHz" (about 14% slower than uncapped: 71.6 against 82.9 tokens/s, `health.jsonl`, 2026-11-18); a run made uncapped is not compared with a capped one.
- In the daytime a job that times this laptop's speed for a claim: run `gpu_run.py check`; the user says whether it runs capped. A capped run is about 15% slower and nothing in its output shows it, so name the cap in the result.
- Daytime capping is the user's choice; never turn it on for them unasked. An overnight self-drive chat follows its own rule.
- If a command says the task could not start, the tasks are not registered: the user runs `scripts/setup-machine.ps1` once from an administrator PowerShell. Never change the power plan or edit settings instead.
- The cap clears on reboot. Another chat's cap benchmark (`gpu_cap_bench.py`) may switch it: do not toggle the cap while `gpu_run.py status` shows a GPU holder named for it.
