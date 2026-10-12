"""Isolated coding-session lifecycle tests."""
import unittest

from orion_v3.work_loop.coding_sessions_v1 import CodingSessionRegistry, SessionState
from orion_v3.work_loop.role_contracts_v1 import Role, TrustedBindings


def scope(revision="a"):
    return TrustedBindings("orion", "T1", "repo", revision, ("new/",), ("frozen/",), "supervised", "limited")


class CodingSessionTests(unittest.TestCase):
    def test_main_and_coding_isolation(self):
        reg = CodingSessionRegistry()
        main = reg.open(Role.MAIN, "main")
        coding = reg.open(Role.GOVERNOR, "coding", scope())
        self.assertTrue(reg.validate(main))
        self.assertTrue(reg.validate(coding, scope()))
        self.assertFalse(reg.validate(coding))
        self.assertEqual(len(reg.snapshot()), 2)

    def test_duplicate_identity_rejected(self):
        reg = CodingSessionRegistry()
        reg.open(Role.MAIN, "main")
        with self.assertRaises(ValueError):
            reg.open(Role.GOVERNOR, "main", scope())

    def test_revision_change_invalidates(self):
        reg = CodingSessionRegistry()
        p = reg.open(Role.CODER, "coder", scope())
        self.assertTrue(reg.validate(p, scope()))
        self.assertFalse(reg.validate(p, scope("b")))

    def test_stale_task_does_not_affect_main(self):
        reg = CodingSessionRegistry()
        main = reg.open(Role.MAIN, "main")
        coding = reg.open(Role.GOVERNOR, "coding", scope())
        self.assertEqual(reg.stale_task("orion", "T1"), 1)
        self.assertFalse(reg.validate(coding, scope()))
        self.assertTrue(reg.validate(main))
        self.assertEqual(reg.snapshot()[1].state, SessionState.STALE)

    def test_close_revokes_session(self):
        reg = CodingSessionRegistry()
        p = reg.open(Role.REVIEWER, "review", scope())
        reg.close("review")
        self.assertFalse(reg.validate(p, scope()))

    def test_tampered_hash_rejected(self):
        from dataclasses import replace
        reg = CodingSessionRegistry()
        p = reg.open(Role.GOVERNOR, "coding", scope())
        self.assertFalse(reg.validate(replace(p, contract_hash="0"*64), scope()))

    def test_coding_role_requires_scope(self):
        reg = CodingSessionRegistry()
        with self.assertRaises(ValueError):
            reg.open(Role.GOVERNOR, "coding")

    def test_wrong_task_scope_rejected(self):
        from dataclasses import replace
        reg = CodingSessionRegistry()
        p = reg.open(Role.CODER, "coder", scope())
        self.assertFalse(reg.validate(p, replace(scope(), task_id="T2")))


if __name__ == "__main__":
    unittest.main()
