import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import thermal_notes_check as c


class ThermalNotesCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        notes = self.tmp / "personal-notes" / "main" / "machine"
        notes.mkdir(parents=True)
        (notes / "laptop-legion-y540.md").write_text("x", encoding="utf-8")
        self.cwd = self.tmp / "proj" / "main"
        self.cwd.mkdir(parents=True)
        self.markers = self.tmp / "markers"

    def payload(self, cmd, sid="s1"):
        return {"tool_input": {"command": cmd}, "cwd": str(self.cwd), "session_id": sid}

    def test_fires_once_per_session(self):
        p = self.payload("python gpu_run.py report --thermal --days 7")
        first = c.run(p, self.markers)
        self.assertIn("laptop-legion-y540.md", first)
        self.assertIsNone(c.run(p, self.markers))
        self.assertIn("laptop-legion-y540.md", c.run(self.payload("powercfg PROCTHROTTLEMAX 99", "s2"), self.markers))

    def test_unrelated_and_notes_file_itself(self):
        self.assertIsNone(c.run(self.payload("git status"), self.markers))
        self.assertIsNone(c.run(self.payload("cat machine/laptop-legion-y540.md thermal.jsonl"), self.markers))

    def test_no_notes_repo(self):
        p = self.payload("tail thermal.jsonl")
        p["cwd"] = tempfile.mkdtemp()
        self.assertIsNone(c.run(p, self.markers))


if __name__ == "__main__":
    unittest.main()
