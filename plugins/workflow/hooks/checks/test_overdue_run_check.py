import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import overdue_run_check as c

NOW = 100_000.0


def hold(command, age_min, session="s1", holder=1, shell=7, tool="Bash", **extra):
    return {"holder": holder, "shell": shell, "tool": tool, "command": command,
            "session": session, "started": NOW - age_min * 60, **extra}


class OverdueRunCheck(unittest.TestCase):
    def setUp(self):
        self.markers = Path(tempfile.mkdtemp())

    def run_check(self, holds, sid="s1"):
        return c.run({"session_id": sid}, holds=holds, now=NOW, marker_dir=self.markers)

    def test_tagged_past_twice_estimate_reports(self):
        out = self.run_check([hold("python t.py  # estimate: 22m", 45)])
        self.assertIn("estimate 22 min", out)
        self.assertIn("45 min", out)
        self.assertIn("TaskStop", out)

    def test_tagged_under_limit_is_quiet(self):
        self.assertIsNone(self.run_check([hold("python t.py  # estimate: 22m", 43)]))

    def test_untagged_uses_20_minute_limit(self):
        self.assertIsNone(self.run_check([hold("python t.py", 19)]))
        self.assertIn("no estimate", self.run_check([hold("python t.py", 21)]))

    def test_one_reminder_per_command(self):
        holds = [hold("python t.py", 30)]
        self.assertIsNotNone(self.run_check(holds))
        self.assertIsNone(self.run_check(holds))
        self.assertIsNotNone(self.run_check([hold("python u.py", 30, holder=2)]))

    def test_other_session_exited_timer_and_unfound_shell_skipped(self):
        self.assertIsNone(self.run_check([hold("python t.py", 90, session="other")]))
        self.assertIsNone(self.run_check([hold("python t.py", 90, exited=NOW)]))
        self.assertIsNone(self.run_check([hold("ScheduleWakeup wait, 60 min: x", 90, tool="ScheduleWakeup", shell=None)]))

    def test_server_gets_no_hold_so_is_never_listed(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import keep_awake
        self.assertFalse(keep_awake.wants_hold("npm run dev"))


if __name__ == "__main__":
    unittest.main()
