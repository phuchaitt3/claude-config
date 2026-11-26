---
topic: dvc-remote-choice
area: Software process
question: Is a DVC remote the standard way to share versioned data between machines, and which remote suits a solo project on two machines (Google Drive, an S3-compatible host, a local or network path)?
checked: 2026-11-27
review_months: 6
status: current
---
# DVC remote choice for a solo, two-machine project

- **Question:** A project tracks data with DVC but has no remote, so the data exists only in one machine's cache. Is a remote the standard fix, and which kind fits one person with two machines? (Separate from `data-versioning-cadence`, which asks when to version, not where the data is stored or how machines share it.)

- **Evidence strength:** official DVC documentation for what remotes are for and how to configure them; a DVC forum thread and an open DVC issue for the Google Drive problem; vendor pages for DagsHub limits (inconsistent). No survey of what solo users choose.

- **Finding:**
  - **A remote is the documented way to share DVC data between machines.** DVC's remote-storage guide says remotes "usually ... will be shared between devices or team members", lists "Centralize or distribute data storage for sharing and collaboration" as a main use, and says to `git commit` `.dvc/config` so every clone gets the remote. Each machine then runs `dvc pull`. A DVC cache with no remote is not shared and has no second copy.
  - **Secrets go in `.dvc/config.local`** (git-ignored, written with `--local`); the remote URL goes in `.dvc/config`. Each clone re-enters its local values.
  - **Supported kinds:** S3 and S3-compatible stores, Azure, Google Cloud Storage, Google Drive, SSH/SFTP, HTTP, WebDAV, HDFS, and local paths ("system directories, mounted drives, network resources e.g. NAS, and other external devices").
  - **Google Drive works but needs your own Google Cloud project today.** The DVC page warns that "the default Google DVC app is affected" by an ongoing issue ("This app is blocked", treeverse/dvc#10516) and calls a custom Google Cloud project "recommended": enable the Drive API, set up the OAuth consent screen, create a Desktop-app OAuth client, then `dvc remote modify <remote> gdrive_client_id ...` and `gdrive_client_secret ...`. The page says the client ID and secret are safe to share in the team; the cached user credentials are a secret and must not be committed. Remote URL: `gdrive://<folder-id>`, the ID taken from the folder's address bar. A service account is the alternative and also needs your own project. Other tools (rclone, Cyberduck) hit the same block and use the same fix.
  - **Google Cloud console layout (2026-11-27 update).** The old "APIs & Services > OAuth consent screen" page is now the **Google Auth Platform** (menu > Google Auth Platform), with Overview, Branding, Audience, Clients, Data Access, Verification Center and Settings. A new project shows "Google Auth Platform not configured yet" and a **Get started** button, which opens a wizard: App Information (name, support email), Audience (Internal or External: Internal needs a Google Workspace organisation, so a personal account picks External), Contact information, then Finish. Test users are added afterwards on the **Audience** page; the OAuth client is made on **Clients > Create client > Application type: Desktop app**. The DVC page still uses the old names.
  - **Testing mode expires tokens after 7 days.** Google's production-readiness page: for an External app in Testing, authorisation and refresh tokens of test users expire 7 days after consent. Selecting **Publish app** on the Audience page moves it to In production, which removes that limit; an app that requests only non-sensitive scopes needs no verification for that, but the Drive scope DVC asks for is sensitive or restricted, so an unverified published app shows an "unverified app" warning that the owner can click past (forum reports; not checked against Google's scope tables here).
  - **DagsHub** gives each repository a DVC remote with no bucket setup; free tier allows private repositories for non-commercial use, up to 2 collaborators. Its storage limit is stated inconsistently (100 GB on the DVC integration page; 20 GB and 200 GB on the pricing page).
  - **Checker's inference** (no source states it): for one person, two machines and data in the tens of megabytes, any of these works; the choice turns on what the person already has. Google Drive costs about 15 minutes of one-time Cloud Console setup; a local or network path needs no outside service but gives no off-site copy unless the drive itself is backed up.

- **Sources:**
  - DVC docs, remote storage (official): https://doc.dvc.org/user-guide/data-management/remote-storage
  - DVC docs, Google Drive remote (official): https://doc.dvc.org/user-guide/data-management/remote-storage/google-drive
  - DVC issue #10516, "This app is blocked" (official tracker): https://github.com/treeverse/dvc/issues/10516
  - DVC forum, "[GDrive] This app is blocked": https://discuss.dvc.org/t/gdrive-this-app-is-blocked/2191
  - rclone forum, same block with Google Drive (other tool): https://forum.rclone.org/t/google-drive-access-blocked-authorization-error/38148
  - Google Cloud Help, Get started with the Google Auth Platform (official): https://support.google.com/cloud/answer/15544987
  - Google Cloud Help, Manage app audience (official): https://support.google.com/cloud/answer/15549945
  - Google Identity, OAuth production readiness (official, 7-day Testing expiry): https://developers.google.com/identity/protocols/oauth2/production-readiness/overview
  - Gemini API OAuth quickstart (official, Clients > Create client > Desktop app): https://ai.google.dev/gemini-api/docs/oauth
  - DagsHub DVC integration (vendor): https://dagshub.com/docs/integration_guide/dvc/
  - DagsHub pricing (vendor): https://dagshub.com/pricing

- **Limits:**
  - The status of issue #10516 was not read directly; the DVC page still links it as ongoing on the check date.
  - The "unverified app" warning after publishing with the Drive scope comes from forum reports, not from Google's scope tables.
  - DagsHub limits are from vendor pages that contradict each other; Backblaze B2 and Cloudflare R2 free tiers were not checked.
  - Nothing found on keeping a DVC remote inside a cloud-sync folder (OneDrive, Google Drive for desktop); the earlier `data-versioning-cadence` entry notes the same gap.

- **Checked:** 2026-11-27
