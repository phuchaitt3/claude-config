import datetime as dt
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import status_check as c

TODAY = dt.date(2026, 11, 27)


def patch(name, *lines):
    return f"diff --git a/{name} b/{name}\n--- a/{name}\n+++ b/{name}\n@@ -1 +1 @@\n" + "\n".join(lines) + "\n"


class FlagPatch(unittest.TestCase):
    def test_added_proposed_without_open_until_is_flagged(self):
        p = patch("docs/adr/0011-bm25.md", "+# 0011: BM25", "+", "+**Status:** Proposed   **Date:** 2026-11-14")
        self.assertEqual(c.flag_patch(p), ["docs/adr/0011-bm25.md"])
        self.assertEqual(c.flag_patch(patch("docs/design/brief.md", "+Status: draft")), ["docs/design/brief.md"])

    def test_open_until_accepted_template_or_non_md_pass(self):
        self.assertEqual(c.flag_patch(patch("a.md", "+**Status:** Proposed   **Open until:** 2026-12-15")), [])
        self.assertEqual(c.flag_patch(patch("a.md", "+**Status:** Proposed", " **Open until:** #117")), [])
        self.assertEqual(c.flag_patch(patch("a.md", "+**Status:** Accepted")), [])
        self.assertEqual(c.flag_patch(patch("a.md", "+**Status:** Proposed | Accepted | Superseded by NNNN")), [])
        self.assertEqual(c.flag_patch(patch("a.md", "+**Status:** draft | decided in ADR NNNN")), [])
        self.assertEqual(c.flag_patch(patch("a.py", "+STATUS: Proposed")), [])

    def test_removed_or_context_status_is_not_flagged(self):
        self.assertEqual(c.flag_patch(patch("a.md", "-**Status:** Proposed", "+**Status:** Accepted")), [])
        self.assertEqual(c.flag_patch(patch("a.md", " **Status:** Proposed", "+a new line")), [])

    def test_several_files(self):
        p = patch("a.md", "+Status: Proposed") + patch("b.md", "+Status: Accepted") + patch("c.md", "+Status: draft")
        self.assertEqual(c.flag_patch(p), ["a.md", "c.md"])


class StaleInFile(unittest.TestCase):
    def test_cases(self):
        self.assertEqual(c.stale_in_file("Status: Proposed. The user decides", TODAY),
                         "Proposed or draft with no Open until")
        self.assertIsNone(c.stale_in_file("**Status:** Proposed  **Open until:** 2026-12-15", TODAY))
        self.assertEqual(c.stale_in_file("**Status:** Proposed  **Open until:** 2026-11-20", TODAY),
                         "Open until 2026-11-20 has passed")
        self.assertIsNone(c.stale_in_file("**Status:** Proposed  **Open until:** #148", TODAY))
        self.assertIsNone(c.stale_in_file("**Status:** Accepted", TODAY))
        self.assertIsNone(c.stale_in_file("**Status:** Proposed | Accepted", TODAY))
        self.assertIsNone(c.stale_in_file("- **Status:** proposed in `Chapter5/chapter5.tex`, not started.", TODAY))


class MergeTarget(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(c.merge_target(["210", "--squash"]), ["210"])
        self.assertEqual(c.merge_target(["--squash", "-R", "o/r", "#210"]), ["210", "-R", "o/r"])
        self.assertEqual(c.merge_target(["--auto", "-b", "body text", "--squash"]), [])


class Run(unittest.TestCase):
    def test_pr_merge_reads_gh_diff(self):
        out = mock.Mock(returncode=0, stdout=patch("docs/adr/0011.md", "+**Status:** Proposed"))
        with mock.patch.object(c.subprocess, "run", return_value=out) as run:
            msg = c.run({"hook_event_name": "PreToolUse", "cwd": ".",
                         "tool_input": {"command": "gh pr merge 210 --squash -R o/r"}})
        self.assertIn("docs/adr/0011.md", msg)
        self.assertEqual(run.call_args[0][0], ["gh", "pr", "diff", "210", "-R", "o/r"])

    def test_other_commands_are_ignored(self):
        with mock.patch.object(c.subprocess, "run") as run:
            self.assertIsNone(c.run({"hook_event_name": "PreToolUse", "tool_input": {"command": "gh pr view 3"}}))
            self.assertIsNone(c.run({"hook_event_name": "PreToolUse", "tool_input": {"command": "git status"}}))
        run.assert_not_called()

    def test_sweep_runs_once_a_day(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "docs").mkdir()
            (repo / "docs" / "a.md").write_text("Status: Proposed\n", encoding="utf-8")
            (repo / "docs" / "b.md").write_text("Status: Accepted\n", encoding="utf-8")

            def fake_git(args, cwd, timeout=10):
                return {"rev-parse": str(repo) + "\n", "ls-files": "docs/a.md\ndocs/b.md\n"}[args[0]]

            with mock.patch.object(c, "_git", fake_git), mock.patch.object(c, "CACHE", repo / "cache.json"):
                first = c._sweep(d, TODAY)
                second = c._sweep(d, TODAY)
                third = c._sweep(d, TODAY + dt.timedelta(days=1))
        self.assertIn("docs/a.md", first)
        self.assertNotIn("docs/b.md", first)
        self.assertIsNone(second)
        self.assertIn("docs/a.md", third)


if __name__ == "__main__":
    unittest.main()
