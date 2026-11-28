---
topic: dvc-what-to-track
area: Software process
question: What belongs in a DVC-tracked folder, and what is redundant there (code copies, caches, training checkpoints)?
checked: 2026-11-28
review_months: 12
status: current
---
# What to track with DVC, and what is redundant

- **Question:** Which files of an ML project's run outputs should DVC keep, and which are redundant? (Separate from `data-versioning-cadence`, which asks when to version, and `dvc-remote-choice`, which asks where.)

- **Evidence strength:** official DVC documentation for the Git/DVC split, `.dvcignore` and `dvc gc`; vendor documentation (read as search summaries only) for checkpoint retention; no data found for a rule on which run outputs to keep.

- **Finding:**
  - **Data and models in DVC, code and small metadata in Git.** The DVC start guide versions the `.dvc` metadata beside the source code and keeps the data itself out of Git.
  - **`.dvcignore` excludes files with `.gitignore` patterns**, and the docs offer it against slow operations on large workspaces (no benchmark). It must sit above a tracked folder, not inside it. A pattern that matches already-tracked files makes DVC treat them as deleted, so the next commit records a version without them; ignored files are not cached, and `dvc repro` / `dvc exp run` may remove them.
  - **Identical files cost cache and remote space once** (content-addressed; DVC forum answer cited in `data-versioning-cadence`). In the workspace they cost space once per copy where DVC falls back to copying; the docs say that fallback is common.
  - **Old objects stay until `dvc gc`.** It needs a scope option, has `--dry`, and with `--cloud` deletes from the remote irreversibly.
  - **Checkpoints:** keeping a short window of recent ones plus the best or final one is a vendor default or option (NVIDIA NeMo AutoModel, AMD Primus). Optimizer and scheduler state are needed only to resume training; without them a resumed run is not the same run.
  - **Checker's inference** (no source states it): `__pycache__/` and `*.pyc` are rebuilt from source and are safe to ignore; library caches (for example Hugging Face `cache-*.arrow`) likewise. Source copies saved inside a run's output are redundant only if the exact code is in a commit; if the run used uncommitted code, the copy is the only record. Intermediate checkpoints and optimizer state of a finished, reported run can go once no resume is planned. Removing files cuts transfer time more than bytes suggest when the removed files are small and many.

- **Sources:**
  - DVC docs, `.dvcignore` files (official): https://doc.dvc.org/user-guide/project-structure/dvcignore-files
  - DVC docs, get started (official): https://doc.dvc.org/start
  - DVC docs, `dvc gc` (official): https://doc.dvc.org/command-reference/gc
  - DVC docs, large dataset optimization (official): https://doc.dvc.org/user-guide/data-management/large-dataset-optimization
  - NeMo AutoModel checkpointing (vendor docs): https://docs.nvidia.com/nemo/automodel/development/checkpointing
  - AMD Primus checkpoint management (vendor docs): https://rocm.docs.amd.com/projects/primus/en/main/04-technical-guides/checkpoint-management.html

- **Limits:** no source names `__pycache__` for DVC; the checkpoint pages are about their own training tools and were not read in full; nothing found on keeping or dropping code snapshots in run outputs.

- **Checked:** 2026-11-28
