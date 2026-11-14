# Lenovo Legion power modes and reading CPU temperature on Windows

- **Question:** How is the power or thermal mode switched on an older Lenovo Legion laptop when Fn+Q does nothing and Vantage shows no thermal-mode setting, and how can a script read CPU temperature on such a machine without administrator rights?
- **Checked:** 2026-11-14
- **Evidence strength:** *official standard* for the Fn+Q key (Lenovo user guide); *vendor or single source* for the third-party toolkit's model list (its own source code); *anecdotal* for mode changes failing (Lenovo community forum); checked on one machine for the WMI interface and Core Temp's shared memory.

## Finding

- **Fn+Q is the documented key.** Lenovo's guide for the Legion Y540 lists Fn+Q as "Adjust thermal mode"; newer Legion guides name Quiet, Balanced and Performance, switched with Fn+Q or in Lenovo Vantage / Legion Zone. The power-button light shows the mode on many Legions (white Balanced, blue Quiet, red Performance per newer guides), but the Y540 guide does not document the colours, and **do not trust them on this model**: on one Y540-17IRH the light was white while the firmware, read by Lenovo Legion Toolkit, reported Performance (checked 2026-11-14). Read the mode from the toolkit instead.
- **When Fn+Q does nothing,** the hotkey software is the usual suspect: the key works through Lenovo's utility and driver stack, and recent Lenovo Vantage builds no longer show the gaming or thermal pages on some older models. Forum reports also say BIOS model or serial data missing after a board swap breaks both Fn+Q and Vantage, and that on some Y540s mode changes made little difference to fan speed.
- **The firmware interface can be checked directly.** The `root\WMI` class `LENOVO_GAMEZONE_DATA` holds `GetSmartFanMode`/`SetSmartFanMode`, fan speeds and CPU/GPU temperatures; it exists when the firmware supports modes. Calling it needs administrator rights.
- **Lenovo Legion Toolkit** (open source, replaces Vantage) checks for that WMI class and matches model names against a list in `Compatibility.cs`: 2020-2022 Legion models are fully listed, and the older `17IR`, `15IR`, `15IC`, `15IK` names are under "limited compatibility". On a Y540-17IRH (a "limited compatibility" name) version 2.26.1 started, showed the power-mode selector and the CLI (`llt.exe feature get power-mode`) read the mode, so for power mode it worked there; it warned that Vantage and ImController were running in the background. The upstream repository was archived by its maintainer on 2025-07-24 ("no longer actively maintained", no security reason given), so 2.26.1 is the final release and the installer is unsigned with no published hash. Its maintainer advises uninstalling or disabling Vantage, the hotkey service and Legion Zone while using it, because they conflict.
- **The Windows power mode is a separate setting** (Settings → System → Power: Best Power Efficiency, Balanced, Best Performance). It changes Windows' processor policy, not the Lenovo fan and power table. Checked on one machine: a GPU drew its full 80 W limit under "Best Power Efficiency".
- **Reading CPU temperature:** Windows' ACPI thermal zone is missing on some laptops. Core Temp publishes per-core temperatures, TjMax and load in a shared-memory block named `CoreTempMappingObject`, which a normal-rights process can read with `OpenFileMapping` (checked 2026-11-14 with Core Temp running elevated). LibreHardwareMonitor's current release did not publish the `root\LibreHardwareMonitor` WMI namespace in the same check; its local web server (`/data.json` on port 8085) is off by default.

## Sources

- [Lenovo Legion Y540 user guide: hidden keys](https://download.lenovo.com/pccbbs/pubs/y540_15ich_irh_17irh/html_en/en/feature_intro_hidden_keys.html) (official docs).
- [Lenovo Legion 5 user guide: system operation modes](https://download.lenovo.com/pccbbs/pubs/legion5_15/html_en/EN/intro_operation_mode_legion.html) (official docs, newer model).
- [Lenovo forum: Legion Y540 fan noise and modes](https://forums.lenovo.com/t5/Gaming-Laptops/Legion-Y540-2060RTX-Fan-noise/m-p/4456116) (vendor community forum).
- [iFixit answer: Fn+Q and Vantage after a motherboard swap](https://ts.ifixit.com/Answers/History/898127) (community).
- [Lenovo Legion Toolkit `Compatibility.cs`](https://github.com/BartoszCichecki/LenovoLegionToolkit/blob/master/LenovoLegionToolkit.Lib/Utils/Compatibility.cs) (project source).
- [LenovoLegionLinux README](https://www.github.com/johnfanv2/LenovoLegionLinux) (project docs; lists Y530/Y540 as an open issue on Linux).

## Limits

Core Temp's shared-memory layout comes from its developer's published SDK and one local check, not a second source. Switching modes with Legion Toolkit on this model was not yet tested when this was written; see the notes below if updated. The power-button colours come from newer Legion guides and were wrong on one Y540.
