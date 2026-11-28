import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import machine_check as c


def prompt(session="s1"):
    return {"hook_event_name": "UserPromptSubmit", "session_id": session}


def fake(flag=128, first=True):
    return dict(battery=lambda: flag, host=lambda: "HOST-1", first=lambda _s: first)


class Machine(unittest.TestCase):
    def test_no_battery_is_the_pc(self):
        out = c.run(prompt(), **fake(flag=128))
        self.assertIn("runs on the PC (HOST-1, no battery)", out)
        self.assertIn("not the laptop's", out)

    def test_battery_is_the_laptop(self):
        out = c.run(prompt(), **fake(flag=1))
        self.assertIn("runs on the laptop (HOST-1, has a battery)", out)
        self.assertIn("not the PC's", out)

    def test_unreadable_is_silent(self):
        self.assertIsNone(c.run(prompt(), **fake(flag=None)))
        self.assertIsNone(c.run(prompt(), **fake(flag=255)))

    def test_later_prompts_and_other_events_are_silent(self):
        self.assertIsNone(c.run(prompt(), **fake(first=False)))
        self.assertIsNone(c.run({"hook_event_name": "Stop", "session_id": "s1"}, **fake()))


if __name__ == "__main__":
    unittest.main()
