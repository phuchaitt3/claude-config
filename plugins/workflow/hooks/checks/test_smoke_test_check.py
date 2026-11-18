import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_test_check as c


def p(cmd):
    return {"tool_input": {"command": cmd}}


class SmokeTestCheck(unittest.TestCase):
    def test_long_untagged_run_gets_the_reminder(self):
        self.assertIn("smoke-test", c.run(p("python bench.py  # estimate: 12m")))
        self.assertIn("smoke-test", c.run(p("python bench.py  # estimate: 1h")))

    def test_short_or_tagged_or_smoke_runs_are_left_alone(self):
        self.assertIsNone(c.run(p("python bench.py  # estimate: 5m")))
        self.assertIsNone(c.run(p("python bench.py  # estimate: 90s")))
        self.assertIsNone(c.run(p("python bench.py  # estimate: 12m  # smoke: --smoke ran 40s, ok")))
        self.assertIsNone(c.run(p("python bench.py  # estimate: 12m  # smoke: none (no short form: one 3-minute training epoch)")))
        self.assertIsNone(c.run(p("python bench.py --smoke  # estimate: 8m")))
        self.assertIsNone(c.run(p("git status")))

    def test_no_command(self):
        self.assertIsNone(c.run({}))
        self.assertIsNone(c.run({"tool_input": {"file_path": "x"}}))


if __name__ == "__main__":
    unittest.main()
