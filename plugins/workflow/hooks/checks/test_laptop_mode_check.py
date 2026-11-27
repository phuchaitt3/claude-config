import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import laptop_mode_check as c


def pre(cmd, tool="PowerShell"):
    return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {"command": cmd}}


def prompt(session="s1"):
    return {"hook_event_name": "UserPromptSubmit", "session_id": session}


def fake(battery=True, cap=False, cpu=100, first=True):
    return dict(battery=lambda: battery, cap=lambda: cap, cpu=lambda: cpu, first=lambda _s: first)


class ModeLine(unittest.TestCase):
    def test_names(self):
        self.assertEqual(c.mode_line(False, 100)[0], "GAME")
        self.assertEqual(c.mode_line(True, 99)[0], "NIGHT")
        self.assertEqual(c.mode_line(True, 100)[0], "MIXED")
        self.assertEqual(c.mode_line(False, None)[0], "MIXED")


class FirstPrompt(unittest.TestCase):
    def test_once_per_session_then_quiet(self):
        out = c.run(prompt(), **fake())
        self.assertIn("GAME", out)
        self.assertIn("game.ps1", out)
        self.assertIsNone(c.run(prompt(), **fake(first=False)))

    def test_no_battery_is_silent(self):
        self.assertIsNone(c.run(prompt(), **fake(battery=False)))


class LongRun(unittest.TestCase):
    def test_long_run_outside_night_mode_gets_the_line(self):
        out = c.run(pre("python run.py  # estimate: 40m"), **fake())
        self.assertIn("night.ps1", out)
        self.assertIn("40 min", out)
        self.assertIn("MIXED", c.run(pre("x  # estimate: 1h", tool="Bash"), **fake(cap=True, cpu=100)))

    def test_quiet_cases(self):
        self.assertIsNone(c.run(pre("python run.py  # estimate: 40m"), **fake(cap=True, cpu=99)))
        self.assertIsNone(c.run(pre("python run.py  # estimate: 10m"), **fake()))
        self.assertIsNone(c.run(pre("python run.py"), **fake()))
        self.assertIsNone(c.run(pre("python run.py  # estimate: 40m", tool="Read"), **fake()))
        self.assertIsNone(c.run(pre("python run.py  # estimate: 40m"), **fake(battery=False)))
        self.assertIsNone(c.run({"hook_event_name": "Stop"}, **fake()))


class RealReaders(unittest.TestCase):
    def test_readers_do_not_raise(self):
        c.has_battery()
        c.gpu_cap_on()
        c.cpu_max_pct()


if __name__ == "__main__":
    unittest.main()
