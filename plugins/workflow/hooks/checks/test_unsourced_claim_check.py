import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import unsourced_claim_check as c


def w(text, path="notes/page.md", key="content"):
    return {"tool_input": {"file_path": path, key: text}}


class UnsourcedClaimCheck(unittest.TestCase):
    def test_unsourced_claims_get_the_reminder(self):
        for text in (
            "Only asked if a test goes into why; no source shows it is.",
            "Nothing shows a test asks it.",
            "No posting names stacks or queues.",
            "This is commonly asked in interviews.",
            "Employers rarely ask about this; it is standard practice.",
        ):
            self.assertIn("unsourced-claim", c.run(w(text)), text)
        self.assertIn("unsourced-claim", c.run(w("no source shows it", key="new_string")))

    def test_sourced_or_marked_claims_are_left_alone(self):
        self.assertIsNone(c.run(w("No source shows it (standard: findings/sql-interview-frequency, checked 2026-11-20).")))
        self.assertIsNone(c.run(w("Nothing shows a test asks it; see findings/entry-level-ml-interview-emphasis.")))
        self.assertIsNone(c.run(w("no source shows it: my judgement, unchecked")))
        self.assertIsNone(c.run(w("No posting names it (prep/mentions.csv rows).")))

    def test_register_files_and_plain_text_are_left_alone(self):
        self.assertIsNone(c.run(w("No source confirmed this.", path="C:/Users/x/claude-config/findings/topic.md")))
        self.assertIsNone(c.run(w("A stack is last in, first out.")))
        self.assertIsNone(c.run({}))
        self.assertIsNone(c.run({"tool_input": {"command": "ls"}}))


if __name__ == "__main__":
    unittest.main()
