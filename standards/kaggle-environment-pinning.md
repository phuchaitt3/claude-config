# Pinning a Kaggle notebook's software environment

**Question:** Can a Kaggle notebook be pinned to the environment it was created with, and can that be set from the command line?

**Finding:**
- Kaggle ties a notebook to a Docker image version. The notebook editor's Settings tab offers a choice between pinning to the image version at creation ("original environment") and always using the latest image. Images are refreshed about every two weeks, mainly to upgrade the preinstalled packages.
- The documented `kernel-metadata.json` fields (used by `kaggle kernels push`, CLI 2.2.5) include no field for the image or environment version, so a notebook pushed from the command line gets the default (latest) image. The documentation says more metadata processing may come.
- Checker's own inference: a CLI-driven run cannot pin the image, so a result that must match an older environment has to pin the packages in the notebook (explicit `pip install name==version`), which does not change the Python version, or pin the image once in the web UI and save the version from there.

**Sources:**
- [How to change the python version in Kaggle Notebook](https://biditsadhukhan.netlify.app/blog/kaggle_env) (community blog; describes the Settings choice).
- [Kaggle tips for running fast.ai notebooks in 2025](https://forums.fast.ai/t/kaggle-tips-for-running-fast-ai-notebooks-in-2025/122272) (community forum; confirms the original/latest choice).
- [Kaggle CLI, kernel metadata fields](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md) (official docs).

**Limits:** The Settings option comes from community posts, not from Kaggle's own documentation, and I did not open the Kaggle UI. Whether a pinned original image still exists years later, and whether a pushed version can be pinned some other way, is not established. Which image a given past run used is not recorded anywhere I found.

**Checked:** 2026-11-12
