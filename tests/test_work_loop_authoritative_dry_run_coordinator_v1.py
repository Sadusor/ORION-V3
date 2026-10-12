import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from orion_v3.work_loop.authorization import issue_authorization
from orion_v3.work_loop.authoritative_dry_run_coordinator_v1 import AuthoritativeDryRunCoordinator
from orion_v3.work_loop.commit_coordinator import CommitCoordinator
from orion_v3.work_loop.contracts import Proposal, RiskClass, WorkState
from orion_v3.work_loop.durable_authorization_ledger_v1 import DurableAuthorizationLedger
from orion_v3.work_loop.gitea_write_preflight_v1 import build_write_intent
from orion_v3.work_loop.vault import ProjectVault

REV = "a"*40
SECRET = b"only-for-tests-123456789"

class Stop:
    def __init__(self): self.active = False
    def stop_requested(self): return self.active

class AuthoritativeDryRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.vault = ProjectVault(root / "vault")
        self.vault.initialize(WorkState("orion", "test", "start", "T1"))
        self.ledger = DurableAuthorizationLedger(root / "auth.sqlite3")
        self.stop = Stop()
        self.commit = CommitCoordinator(self.stop)
        self.coordinator = AuthoritativeDryRunCoordinator(
            vault=self.vault, ledger=self.ledger, stop_source=self.stop,
            commit_coordinator=self.commit, authorization_secret=SECRET)
        self.intent = build_write_intent(project_id="orion", task_id="T1",
            repository="owner/repo", branch="orion/tasks/T1",
            expected_base_sha=REV, operation="commit_files")
        self.proposal = Proposal("orion", "T1", "gitea_write_intent", "owner/repo",
            args={"branch": self.intent.branch, "base_sha": REV,
                  "operation": "commit_files"}, requested_network=True)
        expiry = (datetime.now(timezone.utc)+timedelta(minutes=2)).isoformat()
        self.auth = issue_authorization(self.proposal, RiskClass.YELLOW, expiry,
                                        SECRET, source_revision=REV)

    def tearDown(self): self.tmp.cleanup()

    def check(self, **kw):
        args = dict(intent=self.intent, proposal=self.proposal,
            authorization=self.auth, source_revision=REV,
            expected_generation=self.commit.snapshot())
        args.update(kw)
        return self.coordinator.qualify(**args)

    def test_signed_approval_qualifies_without_write(self):
        self.assertEqual(self.check().status, "QUALIFIED_NO_WRITE")

    def test_stop_source_blocks(self):
        self.stop.active = True
        with self.assertRaises(ValueError): self.check()

    def test_commit_coordinator_stop_blocks(self):
        self.commit.stop()
        with self.assertRaises(ValueError): self.check()

    def test_stale_generation_blocks(self):
        old = self.commit.snapshot()
        self.commit.resume()
        with self.assertRaises(ValueError): self.check(expected_generation=old)

    def test_tampered_approval_denied(self):
        with self.assertRaises(ValueError):
            self.check(authorization=replace(self.auth, signature="0"*64))

    def test_replay_denied(self):
        self.check()
        with self.assertRaises(ValueError): self.check()

    def test_wrong_revision_denied(self):
        with self.assertRaises(ValueError): self.check(source_revision="b"*40)

    def test_frozen_paths_fail_closed(self):
        self.vault._write_state(WorkState("orion", "test", "start", "T1",
                                          frozen_paths=["repo/frozen.py"]))
        with self.assertRaises(ValueError): self.check()

    def test_blocked_vault_denied(self):
        self.vault._write_state(WorkState("orion", "test", "start", "T1", blocked=True))
        with self.assertRaises(ValueError): self.check()

    def test_system_change_denied(self):
        with self.assertRaises(ValueError):
            self.check(proposal=replace(self.proposal, requested_system_change=True))

    def test_wrong_task_denied(self):
        with self.assertRaises(ValueError):
            self.check(intent=replace(self.intent, task_id="T2"))


if __name__ == "__main__": unittest.main()
