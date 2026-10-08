"""Fake existing-connector integration tests: zero external calls."""
import unittest
from .multi_ai_existing_reviewer import run_council, _responses

class FakeConnector:
    def __init__(self):
        self.prompts = []
        self.ids = []
    def start(self, prompt, reviewer_ids, popup_windows=False):
        self.prompts.append(prompt)
        self.ids = reviewer_ids
    def view(self):
        return {"state": "completed", "reviewers": [
            {"reviewer_id": name, "state": "completed", "output": name + " response " + str(len(self.prompts))}
            for name in self.ids]}
    def stop(self):
        raise AssertionError("completed round must not be stopped")

class Tests(unittest.TestCase):
    def test_two_rounds_existing_connector(self):
        c = FakeConnector()
        p = run_council(connector=c, reviewer_ids=["cloud-a", "cloud-b"],
                        project_id="p", task_id="t", objective="tiny calculator",
                        stop_requested=lambda: False)
        self.assertEqual(p.stage, "plan")
        self.assertEqual(len(p.proposals), 2)
        self.assertEqual(len(p.critiques), 2)
        self.assertEqual(len(c.prompts), 2)
        self.assertNotIn("cloud-a response", c.prompts[0])
        self.assertIn("cloud-a response", c.prompts[1])
        self.assertEqual(p.approved_digest, "")
    def test_missing_attribution_fails_closed(self):
        with self.assertRaises(ValueError):
            _responses({"reviewers": [{"state": "completed", "output": "x"}]}, ("a", "b"))
    def test_duplicate_identity_fails_closed(self):
        with self.assertRaises(ValueError):
            run_council(connector=FakeConnector(), reviewer_ids=["a", "a"],
                        project_id="p", task_id="t", objective="test", stop_requested=lambda: False)
    def test_stop_prevents_cloud_call(self):
        c = FakeConnector()
        with self.assertRaises(RuntimeError):
            run_council(connector=c, reviewer_ids=["a", "b"],
                        project_id="p", task_id="t", objective="test", stop_requested=lambda: True)
        self.assertEqual(c.prompts, [])

if __name__ == "__main__":
    unittest.main()
