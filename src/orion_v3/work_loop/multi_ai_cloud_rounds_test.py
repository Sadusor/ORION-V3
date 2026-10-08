"""Offline fake-provider verification of independent and cross-review rounds."""
import unittest
from .multi_ai_cloud_rounds import ModelEndpoint, brainstorm

class CloudRoundsTests(unittest.TestCase):
    def test_two_models_and_cross_review(self):
        calls = []
        def fake(name):
            def invoke(prompt):
                calls.append((name, prompt))
                return name + " critique" if "CROSS-REVIEW ROUND" in prompt else name + " independent proposal"
            return invoke
        p = brainstorm(project_id="p", task_id="t", objective="small calculator",
                       models=[ModelEndpoint("a", fake("a")), ModelEndpoint("b", fake("b"))],
                       stop_requested=lambda: False)
        self.assertEqual(p.stage, "plan")
        self.assertEqual(len(p.proposals), 2)
        self.assertEqual(len(p.critiques), 2)
        self.assertEqual(len(calls), 4)
        self.assertNotIn("independent proposal", calls[0][1])
        self.assertNotIn("independent proposal", calls[1][1])
        self.assertIn("a independent proposal", calls[2][1])
        self.assertIn("b independent proposal", calls[2][1])
        self.assertIn("a independent proposal", calls[3][1])
    def test_duplicate_models_denied_before_call(self):
        with self.assertRaises(ValueError):
            brainstorm(project_id="p", task_id="t", objective="task",
                       models=[ModelEndpoint("a", lambda _: "x"), ModelEndpoint("a", lambda _: "y")],
                       stop_requested=lambda: False)
    def test_stop_before_call(self):
        called = []
        def invoke(_):
            called.append(True)
            return "response"
        with self.assertRaises(RuntimeError):
            brainstorm(project_id="p", task_id="t", objective="task",
                       models=[ModelEndpoint("a", invoke), ModelEndpoint("b", invoke)],
                       stop_requested=lambda: True)
        self.assertFalse(called)
    def test_empty_model_output_denied(self):
        with self.assertRaises(ValueError):
            brainstorm(project_id="p", task_id="t", objective="task",
                       models=[ModelEndpoint("a", lambda _: ""), ModelEndpoint("b", lambda _: "ok")],
                       stop_requested=lambda: False)
    def test_no_automatic_approval(self):
        p = brainstorm(project_id="p", task_id="t", objective="task",
                       models=[ModelEndpoint("a", lambda _: "a"), ModelEndpoint("b", lambda _: "b")],
                       stop_requested=lambda: False)
        self.assertEqual(p.approved_digest, "")
        self.assertEqual(p.stage, "plan")

if __name__ == "__main__":
    unittest.main()
