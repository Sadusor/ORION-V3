import json
import tempfile
import unittest
from pathlib import Path
from orion_v3.work_loop.council_checkpoint import append_checkpoint

class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"evidence.jsonl"
    def append(self, status="COMPLETED"):
        return append_checkpoint(path=self.path,task_id="task",slot_id="author-a",
            provider="groq",model="gpt-oss",family="gpt-oss",status=status)
    def test_first(self):
        digest=self.append()
        self.assertEqual(len(digest),64)
    def test_chain(self):
        first=self.append("RATE_LIMIT")
        self.append()
        records=[json.loads(x) for x in self.path.read_text().splitlines()]
        self.assertEqual(records[1]["previous"],first)
    def test_tamper(self):
        self.append()
        self.path.write_text(self.path.read_text().replace("COMPLETED","FAKED"))
        with self.assertRaises(ValueError):self.append()
    def test_reject_control_characters(self):
        with self.assertRaises(ValueError):
            append_checkpoint(path=self.path,task_id="task\nSECRET",slot_id="a",
                provider="p",model="m",family="f",status="COMPLETED")
    def test_symlink(self):
        other=Path(self.temp.name)/"other"
        other.write_text("")
        link=Path(self.temp.name)/"link"
        try:link.symlink_to(other)
        except (OSError,NotImplementedError):self.skipTest("symlink unsupported")
        with self.assertRaises(ValueError):
            append_checkpoint(path=link,task_id="task",slot_id="a",provider="p",
                              model="m",family="f",status="COMPLETED")

if __name__=="__main__":unittest.main()
