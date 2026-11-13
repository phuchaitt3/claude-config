# Data versioning cadence (DVC)

- **Question:** With data kept out of git and versioned by DVC, must every change to the data folder, however small, be followed by `dvc commit` and `dvc push`? What do projects do instead?

- **Finding:**
  - **DVC records a version only when told to.** The getting-started guide shows the loop as change the data, `dvc add` or `dvc commit`, `dvc push`, then `git commit` of the `.dvc` pointer. A change that skips this loop exists only in the working folder.
  - **Automation is partial.** `dvc install` adds three git hooks:
    - post-checkout runs `dvc checkout`;
    - pre-push runs `dvc push`;
    - pre-commit runs only `dvc status`, as a reminder, and does not run `dvc commit` itself.

    A pipeline (`dvc.yaml` with `dvc repro`) records its outputs automatically, but only for files the pipeline produces.
  - **Small, often-edited files cost the most.** DVC stores each version of a file whole. A DVC maintainer confirmed on the forum that a tiny edit to a small file is stored as a full new copy; only identical files are stored once.
  - **What DVC is for.** Datasets, models and other large outputs that git handles badly. Secondary guides say to use it for data and processing outputs, not as a general store.
  - **Checker's inference** (no source states it as a rule):
    - The industry pattern is to version data at meaningful points: a new dataset, a finished run, or a result that a commit or report depends on. Not after every edit.
    - Small text that changes often, such as notes or coordination files, belongs in git, either the project's repository or a private one of its own, where diffs are cheap and commits are routine.
    - Backup of files between versions is a separate job, for a sync or backup tool, not for DVC.

- **Sources:**
  - DVC docs, `dvc install` (official): https://doc.dvc.org/command-reference/install
  - DVC docs, get started (official): https://github.com/treeverse/dvc.org/blob/main/content/docs/start/index.md
  - DVC forum, "Storage usage for large file versioning" (answer from the DVC team): https://discuss.dvc.org/t/storage-usage-for-large-file-versioning/951
  - Theodo blog, automating DVC with a Makefile, reporting slow per-commit hooks (practitioner): https://www.theodo.com/blog/automate-dvc-pipelines-reproduction-with-makefile
  - Medium (LittleBigCode), DVC scope (secondary): https://medium.com/hub-by-littlebigcode/mlops-how-dvc-smartly-manages-your-data-sets-for-training-your-machine-learning-models-on-top-of-b73857e54e52

- **Limits:**
  - No official DVC page says how often to version. The cadence and the "small notes go in git" points are the checker's inference from how the tool works.
  - The forum answer is from 2021. It mentions plans for chunked storage that were not checked here.
  - Nothing found on keeping a DVC remote in a cloud-sync folder such as OneDrive (sync conflicts, version history).

- **Checked:** 2026-11-08
