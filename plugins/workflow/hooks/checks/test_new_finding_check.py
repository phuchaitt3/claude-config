import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import new_finding_check as c


def entry(d, topic, question):
    (d / f"{topic}.md").write_text(f"---\ntopic: {topic}\nquestion: {question}\n---\n", encoding="utf-8")


class NewFindingCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.reg = Path(self.tmp.name) / "findings"
        self.reg.mkdir()
        entry(self.reg, "resume-bullet-order", "Which bullet goes first on a resume?")
        entry(self.reg, "resume-bullet-density", "How many bullets per project?")
        entry(self.reg, "resume-bold-text", "Is bold text on a resume read by recruiters?")
        entry(self.reg, "gpu-cooling", "How to keep a laptop GPU cool?")
        (self.reg / "README.md").write_text("index", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def w(self, name, content=""):
        return {"tool_input": {"file_path": str(self.reg / name), "content": content}}

    def test_new_entry_lists_nearest_and_cluster_note(self):
        out = c.run(self.w("resume-bullet-length.md", "---\nquestion: How long should a resume bullet be?\n---"))
        self.assertIn("new-finding:", out)
        self.assertIn("resume-bullet-order", out)
        self.assertNotIn("gpu-cooling (", out.split("Add a dated")[0].split("\n")[1])
        self.assertIn("3 entries already start with `resume-`", out)

    def test_at_most_three_listed(self):
        out = c.run(self.w("resume-x.md"))
        self.assertEqual(out.count("\n  - "), 3)

    def test_unrelated_new_entry_still_gets_the_rule(self):
        self.assertIn("two sourced lines", c.run(self.w("mouse-click-lock.md")))

    def test_left_alone(self):
        self.assertIsNone(c.run(self.w("resume-bold-text.md")))  # existing file
        self.assertIsNone(c.run(self.w("README.md")))
        self.assertIsNone(c.run({"tool_input": {"file_path": str(self.reg.parent / "notes.md")}}))
        self.assertIsNone(c.run({"tool_input": {"file_path": str(self.reg / "x.txt")}}))
        self.assertIsNone(c.run({}))

    def test_empty_register(self):
        e = Path(self.tmp.name) / "other" / "findings"
        e.mkdir(parents=True)
        self.assertIsNone(c.run({"tool_input": {"file_path": str(e / "a.md")}}))


if __name__ == "__main__":
    unittest.main()
