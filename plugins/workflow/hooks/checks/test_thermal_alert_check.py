import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import thermal_alert_check as c

NOW = datetime(2026, 11, 18, 20, 0).astimezone()


def ev(event, minutes_ago, **kw):
    return json.dumps({"ts": (NOW - timedelta(minutes=minutes_ago)).isoformat(timespec="seconds"), "event": event, **kw})


class ThermalAlertCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.log = self.tmp / "events.jsonl"
        self.markers = self.tmp / "m"

    def go(self, sid="s1"):
        return c.run({"session_id": sid}, self.markers, self.log, NOW)

    def test_new_warn_is_reported_once_per_session(self):
        self.log.write_text(chr(10).join([ev("start", 30), ev("thermal_warn", 10, temp_c=82, purpose="train")]))
        first = self.go()
        self.assertIn("warned", first)
        self.assertIn("82", first)
        self.assertIsNone(self.go())
        self.assertIn("warned", self.go("s2"))  # another chat is told too

    def test_stop_is_named_and_later_events_reported_again(self):
        self.log.write_text(ev("thermal_warn", 30))
        self.go()
        self.log.write_text(self.log.read_text() + chr(10) + ev("thermal_stop", 5, temp_c=93))
        self.assertIn("STOPPED", self.go())

    def test_old_or_absent_events_are_ignored(self):
        self.assertIsNone(self.go())
        self.log.write_text(ev("thermal_warn", 300))
        self.assertIsNone(self.go())
        self.log.write_text("not json" + chr(10) + ev("start", 1))
        self.assertIsNone(self.go())


if __name__ == "__main__":
    unittest.main()
