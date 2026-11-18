---
name: gpu-cap
description: Load when the user asks to cap, throttle or cool the laptop GPU, wants a quieter or cooler laptop for a heavy job, asks to lift or remove the GPU clock cap, or asks whether the cap is on; also before a job that times this laptop's speed. How to switch the GPU clock cap on, off or read its state with one command.
---

# GPU clock cap (laptop)

Added 2026-11-18 (user's request, claude-config issue #22). Locks the laptop GPU at 1000-1350 MHz: about 10 °C cooler, 45% less power and about 15% slower than uncapped (20-minute test, 2026-11-17). The tasks behind it are registered by `setup-machine.ps1`; the overnight rule is in `workflow:self-drive` ("GPU clock cap").

**Commands** (one call each; prints ON or OFF, exit 1 if it did not take effect):

- `python ~/claude-config/scripts/gpu_run.py cap on` — cooler and quieter, slower.
- `python ~/claude-config/scripts/gpu_run.py cap off` — full speed.
- `python ~/claude-config/scripts/gpu_run.py cap status` — which one it is now.

**When to use which**

- The user says "cool it down", "quiet mode", "cap the GPU": `cap on`. "Full speed", "lift the cap", "I am going to game": `cap off`. "Is the cap on?": `cap status`.
- Before any job that times this laptop's speed (a benchmark, a speed claim), run `gpu_run.py check`; if it says the cap is left on, `cap off` and run `check` again. A capped run is about 15% slower and nothing in its output shows it.
- Daytime capping is the user's choice; never turn it on for them unasked. An overnight self-drive chat follows its own rule.
- If a command says the task could not start, the tasks are not registered: the user runs `scripts/setup-machine.ps1` once from an administrator PowerShell. Never change the power plan or edit settings instead.
- The cap clears on reboot. Another chat's cap benchmark (`gpu_cap_bench.py`) may switch it: do not toggle the cap while `gpu_run.py status` shows a GPU holder named for it.
