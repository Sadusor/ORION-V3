import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from orion_v3.work_loop.authorization import issue_authorization
from orion_v3.work_loop.contracts import Proposal, RiskClass
from orion_v3.work_loop.durable_authorization_ledger_v1 import DurableAuthorizationLedger
from orion_v3.work_loop.gitea_dry_run_boundary_v1 import GiteaDryRunBoundary
from orion_v3.work_loop.gitea_write_preflight_v1 import build_write_intent

SECRET = b"test-only-key"
REV = "a" * 40


def scenario():
    intent = build_write_intent(
        project_id="orion", task_id="T1", repository="owner/repo",
        branch="orion/tasks/T1", expected_base_sha=REV, operation="commit_files",
    )
    proposal = Proposal(
        "orion", "T1", "gitea_write_intent", "owner/repo",
        args={"branch": intent.branch, "base_sha": REV, "operation": "commit_files"},
        requested_network=True,
    )
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
    authorization = issue_authorization(
        proposal, RiskClass.YELLOW, expiry, SECRET, source_revision=REV,
    )
    return dict(
        intent=intent, proposal=proposal, authorization=authorization,
        secret=SECRET, source_revision=REV, stop_requested=False,
        owner_approved=True, frozen_paths_clear=True,
    )


class GiteaDryRunBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "ledger.sqlite3"
        self.boundary = GiteaDryRunBoundary(DurableAuthorizationLedger(self.path))

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_receipt_only(self):
        receipt = self.boundary.qualify(**scenario())
        self.assertEqual(receipt.status, "DRY_RUN_ONLY")
        self.assertEqual(receipt.source_revision, REV)

    def test_stop_denied_without_nonce_consumption(self):
        args = scenario()
        args["stop_requested"] = True
        with self.assertRaises(ValueError):
            self.boundary.qualify(**args)
        args["stop_requested"] = False
        self.assertEqual(self.boundary.qualify(**args).status, "DRY_RUN_ONLY")

    def test_owner_approval_required(self):
        args = scenario()
        args["owner_approved"] = False
        with self.assertRaises(ValueError):
            self.boundary.qualify(**args)

    def test_frozen_paths_clear_required(self):
        args = scenario()
        args["frozen_paths_clear"] = False
        with self.assertRaises(ValueError):
            self.boundary.qualify(**args)

    def test_tampered_branch_denied(self):
        args = scenario()
        args["intent"] = replace(args["intent"], branch="main")
        with self.assertRaises(ValueError):
            self.boundary.qualify(**args)

    def test_revision_mismatch_denied(self):
        args = scenario()
        args["source_revision"] = "b"*40
        with self.assertRaises(ValueError):
            self.boundary.qualify(**args)

    def test_replay_denied_same_boundary(self):
        args = scenario()
        self.boundary.qualify(**args)
        with self.assertRaises(ValueError):
            self.boundary.qualify(**args)

    def test_replay_denied_after_new_boundary(self):
        args = scenario()
        self.boundary.qualify(**args)
        fresh = GiteaDryRunBoundary(DurableAuthorizationLedger(self.path))
        with self.assertRaises(ValueError):
            fresh.qualify(**args)

    def test_tampered_signature_denied(self):
        args = scenario()
        args["authorization"] = replace(args["authorization"], signature="0"*64)
        with self.assertRaises(ValueError):
            self.boundary.qualify(**args)


if __name__ == "__main__":
    unittest.main()
