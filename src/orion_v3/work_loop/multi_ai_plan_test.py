"""Offline regression for multi-model planning; never executes model-generated code."""
import unittest
from .multi_ai_plan import MultiAIPlan

def initial():
    return MultiAIPlan("project", "task", "build a tiny app")

def independent():
    return initial().submit_independent((("model-a", "SQLite"), ("model-b", "JSON")))

def reviewed():
    return independent().submit_cross_review((("model-a", "JSON persistence risk"), ("model-b", "SQLite complexity risk")))

class MultiAIPlanTests(unittest.TestCase):
    def test_two_distinct_models_required(self):
        with self.assertRaises(ValueError):
            initial().submit_independent((("a", "one"),))
        with self.assertRaises(ValueError):
            initial().submit_independent((("a", "one"), ("a", "two")))
    def test_empty_proposal_rejected(self):
        with self.assertRaises(ValueError):
            initial().submit_independent((("a", ""), ("b", "ok")))
    def test_no_skipping_critique(self):
        with self.assertRaises(ValueError):
            independent().propose_plan("go")
    def test_all_models_review(self):
        with self.assertRaises(ValueError):
            independent().submit_cross_review((("model-a", "ok"),))
    def test_wrong_reviewer_rejected(self):
        with self.assertRaises(ValueError):
            independent().submit_cross_review((("model-a", "ok"), ("model-c", "ok")))
    def test_owner_approval_requires_exact_digest(self):
        p = reviewed().propose_plan("SQLite, tests", ("DB size disputed",))
        with self.assertRaises(ValueError):
            p.owner_decide("approve", "wrong")
        approved = p.owner_decide("approve", p.plan_digest)
        self.assertEqual(approved.stage, "approved_for_patch_proposals")
        self.assertEqual(approved.approved_digest, p.plan_digest)
    def test_rejection(self):
        p = reviewed().propose_plan("plan")
        self.assertEqual(p.owner_decide("reject", p.plan_digest).stage, "rejected")
    def test_digest_binds_disagreements(self):
        a = reviewed().propose_plan("plan", ("a",))
        b = reviewed().propose_plan("plan", ("b",))
        self.assertNotEqual(a.plan_digest, b.plan_digest)
    def test_round_cannot_be_replayed(self):
        with self.assertRaises(ValueError):
            independent().submit_independent((("c", "x"), ("d", "y")))
    def test_plan_cannot_execute(self):
        self.assertFalse(hasattr(reviewed().propose_plan("plan"), "execute"))

if __name__ == "__main__":
    unittest.main()
