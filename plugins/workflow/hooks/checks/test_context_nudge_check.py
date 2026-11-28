import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import context_nudge_check as c


def reply(ctx, sidechain=False):
    return {"type": "assistant", "isSidechain": sidechain,
            "message": {"usage": {"input_tokens": 2, "cache_read_input_tokens": ctx - 2}}}


class ContextNudgeCheck(unittest.TestCase):
    def run_on(self, *entries):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "t.jsonl"
            path.write_text("".join(json.dumps(e, separators=(",", ":")) + "\n" for e in entries), encoding="utf-8")
            return c.run({"transcript_path": str(path)})

    def test_over_the_limit_reports_the_size(self):
        text = self.run_on(reply(230_000))
        self.assertIn("230k", text)
        self.assertIn("/clear", text)

    def test_at_or_under_the_limit_is_silent(self):
        self.assertIsNone(self.run_on(reply(200_000)))
        self.assertIsNone(self.run_on(reply(60_000)))

    def test_only_the_last_main_thread_reply_counts(self):
        self.assertIsNone(self.run_on(reply(250_000), reply(60_000)))
        self.assertIsNone(self.run_on(reply(60_000), reply(250_000, sidechain=True)))

    def test_silent_right_after_compaction_then_counts_again(self):
        boundary = {"type": "system", "subtype": "compact_boundary"}
        summary = {"type": "user", "isCompactSummary": True, "message": {"content": "summary"}}
        self.assertIsNone(self.run_on(reply(250_000), boundary, summary))
        self.assertIsNotNone(self.run_on(reply(250_000), boundary, summary, reply(220_000)))

    def test_missing_transcript_is_silent(self):
        self.assertIsNone(c.run({}))
        self.assertIsNone(c.run({"transcript_path": "no-such-file.jsonl"}))


if __name__ == "__main__":
    unittest.main()
