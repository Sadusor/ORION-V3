import tempfile
import unittest
from dataclasses import replace

from orion_v3.work_loop.contracts import Proposal, WorkState
from orion_v3.work_loop.gitea_write_preflight_v1 import build_write_intent
from orion_v3.work_loop.gitea_vault_preflight_v1 import inspect_live_preflight
from orion_v3.work_loop.vault import ProjectVault

REV = "a"*40


class GiteaVaultPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = ProjectVault(self.tmp.name)
        self.vault.initialize(WorkState("orion", "test", "start", "T1"))
        self.intent = build_write_intent(project_id="orion", task_id="T1",
            repository="owner/repo", branch="orion/tasks/T1",
            expected_base_sha=REV, operation="commit_files")
        self.proposal = Proposal("orion", "T1", "gitea_write_intent", "owner/repo",
            args={"branch": self.intent.branch, "base_sha": REV,
                  "operation": "commit_files"}, requested_network=True)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, **kwargs):
        args = dict(vault=self.vault, intent=self.intent, proposal=self.proposal,
            source_revision=REV, stop_is_clear=lambda: True,
            owner_approval_is_valid=lambda project, task, digest: True,
            frozen_path_check=lambda intent, frozen: True)
        args.update(kwargs)
        return inspect_live_preflight(**args)

    def test_canonical_task_passes_preflight_only(self):
        self.assertEqual(self.check().verdict, "PREFLIGHT_ONLY")

    def test_wrong_task_denied(self):
        with self.assertRaises(ValueError):
            self.check(intent=replace(self.intent, task_id="T2"))

    def test_wrong_revision_denied(self):
        with self.assertRaises(ValueError):
            self.check(source_revision="b"*40)

    def test_stop_denied(self):
        with self.assertRaises(ValueError):
            self.check(stop_is_clear=lambda: False)

    def test_owner_approval_denied(self):
        with self.assertRaises(ValueError):
            self.check(owner_approval_is_valid=lambda *args: False)

    def test_frozen_path_denied(self):
        with self.assertRaises(ValueError):
            self.check(frozen_path_check=lambda *args: False)

    def test_policy_rejects_system_change(self):
        with self.assertRaises(ValueError):
            self.check(proposal=replace(self.proposal, requested_system_change=True))

    def test_stop_rechecked(self):
        calls = iter([True, False])
        with self.assertRaises(ValueError):
            self.check(stop_is_clear=lambda: next(calls))

    def test_vault_blocked_denied(self):
        from orion_v3.work_loop.contracts import WorkState
        self.vault._write_state(WorkState("orion", "test", "start", "T1", blocked=True))
        with self.assertRaises(ValueError):
            self.check()


if __name__ == "__main__":
    unittest.main()
