# Pinning a Kaggle notebook's software environment

**Question:** Can a Kaggle notebook be pinned to the environment it was created with, and can that be set from the command line?

**Finding:**
- Kaggle ties a notebook to a Docker image version. In the notebook editor, Settings > Environment Preferences offers two choices: "Pin to original environment" and "Always use latest environment" (confirmed on a screenshot of the editor, 2026-11-12, where "Pin to original environment" was ticked). Images are refreshed about every two weeks, mainly to upgrade the preinstalled packages.
- Checker's own inference: "original" means the image current when that notebook was created, not an image chosen by date. A notebook created in 2026-10 is therefore pinned to the 2026-10 image, and a result that needs an older environment has to come from a notebook created then (or from one kept pinned since), or from explicit package pins. The Python version follows the image.
- The documented `kernel-metadata.json` fields (used by `kaggle kernels push`, CLI 2.2.5) include no field for the image or environment version, so a notebook pushed from the command line gets the default (latest) image. The documentation says more metadata processing may come.
- Checker's own inference: the CLI offers no way to choose the image. A pushed new version of an existing notebook appears to keep that notebook's setting, but this was not tested; packages can be pinned in the notebook (explicit `pip install name==version`), which does not change the Python version.

**Sources:**
- Screenshot of the Kaggle notebook editor's Settings menu, 2026-11-12 (first-hand, from the user).
- [How to change the python version in Kaggle Notebook](https://biditsadhukhan.netlify.app/blog/kaggle_env) (community blog; describes the Settings choice).
- [Kaggle tips for running fast.ai notebooks in 2025](https://forums.fast.ai/t/kaggle-tips-for-running-fast-ai-notebooks-in-2025/122272) (community forum; confirms the original/latest choice).
- [Kaggle CLI, kernel metadata fields](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md) (official docs).

**Limits:** The menu labels are from a user's screenshot and community posts, not Kaggle's own documentation. What "original" means precisely, whether an old image stays available for years, and whether a CLI push keeps the setting were not tested. Which image a given past run used is not recorded anywhere I found.

**Checked:** 2026-11-12
