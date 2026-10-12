import unittest
from orion_v3.work_loop.offline_coding_council_v1 import run_offline_council
from orion_v3.work_loop.role_contracts_v1 import Role, TrustedBindings

class OfflineCouncilTests(unittest.TestCase):
    def setUp(self):
        self.bindings = TrustedBindings("orion", "T1", "owner/repo", "a"*40,
            ("src/new.py",), ("src/frozen.py",), "dry_run", "zero_cost")
        self.calls = []
        self.stopped = False

    def invoke(self, role, system, question):
        self.calls.append((role, system, question))
        return {Role.GOVERNOR: "PLAN", Role.CODER: "PATCH", Role.REVIEWER: "REVIEW"}[role]

    def run(self, **kwargs):
        args = dict(bindings=self.bindings, objective="Add isolated test feature",
            invoke=self.invoke, stop_requested=lambda: self.stopped)
        args.update(kwargs)
        return run_offline_council(**args)

    def test_full_four_turn_cycle(self):
        result = self.run()
        self.assertEqual([x[0] for x in self.calls],
            [Role.GOVERNOR, Role.CODER, Role.REVIEWER, Role.GOVERNOR])
        self.assertEqual(result.status, "REVIEWED_NOT_EXECUTED")
        self.assertEqual(result.coder_patch, "PATCH")

    def test_scope_in_every_prompt(self):
        self.run()
        for _, system, _ in self.calls:
            self.assertIn("src/frozen.py", system)
            self.assertIn("orion", system)

    def test_reviewer_sees_patch(self):
        self.run()
        self.assertIn("PATCH", self.calls[2][2])

    def test_governor_receives_review(self):
        self.run()
        self.assertIn("REVIEW", self.calls[3][2])

    def test_stop_before_start(self):
        self.stopped = True
        with self.assertRaises(ValueError): self.run()
        self.assertFalse(self.calls)

    def test_stop_during_model(self):
        def invoke(*args):
            self.stopped = True
            return "PLAN"
        with self.assertRaises(ValueError): self.run(invoke=invoke)
        self.assertEqual(len(self.calls), 0)

    def test_empty_model_output_denied(self):
        with self.assertRaises(ValueError):
            self.run(invoke=lambda *args: "")

    def test_oversized_output_denied(self):
        with self.assertRaises(ValueError):
            self.run(invoke=lambda *args: "x"*12001)

    def test_invalid_objective_denied(self):
        with self.assertRaises(ValueError): self.run(objective="")

    def test_no_executor_or_approval_claim(self):
        self.assertEqual(self.run().status, "REVIEWED_NOT_EXECUTED")

if __name__ == "__main__": unittest.main()
