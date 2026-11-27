---
topic: onedrive-signin-windows10
area: Software process
question: On Windows 10, the OneDrive "Sign in" button closes the window and nothing happens. What causes it and what fixes it?
checked: 2026-11-27
review_months: 6
status: current
---
# OneDrive sign-in does nothing on Windows 10

- **Question:** After running the `OneDriveSetup.exe` that ships with Windows, the app says "OneDrive isn't connected"; pressing "Sign in" closes the window and nothing follows. (A separate entry because no other one covers the OneDrive app; `dvc-remote-choice` asks which remote to use, not why a client fails to sign in.)

- **Evidence strength:** official Microsoft pages for versions and update rules; **none found that names this symptom or its fix**. The fixes come from third-party guides and community threads. One local observation (below).

- **Finding:**
  - **The setup file bundled in `C:\Windows\SysWOW64` can be years old.** Observed 2026-11-27 on Windows 10 22H2: it installed 21.220.1024.0005, while the current release was 26.212.1029.0006. Run again after install, it had not moved itself to a new version within a few minutes.
  - **Windows 10 needs 22H2 to get updates.** Microsoft: "The OneDrive sync app requires Windows 10 22H2 or Windows 11 to receive updates"; after 2026-08-15, earlier Windows 10 versions stay on the installed version.
  - **Updating through the package manager works from a normal shell:** `winget install --id Microsoft.OneDrive --exact` upgraded 21.220 to 26.212 in place (observed; hash verified by winget). It left the app stopped, so start it afterwards.
  - **Order to try (checker's inference):** (1) update the app; (2) reset it, Win+R, `%localappdata%\Microsoft\OneDrive\onedrive.exe /reset`; (3) with the app closed, rename `%localappdata%\Microsoft\OneDrive\settings\PreSignInSettingsConfig.json`; (4) remove OneDrive entries in Credential Manager; (5) check antivirus, firewall or VPN. A reset disconnects sync, so check nothing is waiting to upload first.
  - The reset path differs when the app is installed under `Program Files`; use the path where `OneDrive.exe` is.
  - **Whether the update fixes the symptom is not yet confirmed** (the observation stops at the successful upgrade).

- **Sources:**
  - Microsoft Learn, OneDrive sync release notes (official, versions and Windows 10 rule): https://learn.microsoft.com/en-us/sharepoint/sync-release-notes
  - Microsoft Learn, sync app update process (official, minimum-version mechanics): https://learn.microsoft.com/en-us/sharepoint/sync-client-update-process
  - WPS guide, sign-in button not working (vendor of another product; reset and PreSignInSettingsConfig): https://www.wps.com/office-quick-solution/login-account-issues/how-to-fix-the-onedrive-sign-in-button-not-working/
  - Microsoft Tech Community, "OneDrive stuck on signing in" (community; one user fixed it by installing the latest app; a related symptom, not this one): https://techcommunity.microsoft.com/discussions/onedriveforbusiness/onedrive-stuck-on-signing-in/4023276

- **Limits:**
  - No source states a minimum version for signing in, so "the old build is the cause" is unproven.
  - Microsoft's "Reset OneDrive" support article was not read (the fetch was denied), so the reset command and its effect rest on search summaries.
  - The vendor and community pages were read as search summaries, not in full.
  - One machine, one personal account.

- **Checked:** 2026-11-27
