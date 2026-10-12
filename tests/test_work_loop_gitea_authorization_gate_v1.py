import unittest
from datetime import datetime, timedelta, timezone
from dataclasses import replace
from orion_v3.work_loop.authorization import issue_authorization
from orion_v3.work_loop.contracts import Proposal, RiskClass
from orion_v3.work_loop.gitea_write_preflight_v1 import build_write_intent
from orion_v3.work_loop.gitea_authorization_gate_v1 import GiteaAuthorizationGate

SECRET = b"test-only-secret"


def setup():
    intent = build_write_intent(project_id="orion", task_id="T1", repository="owner/repo",
        branch="orion/tasks/T1", expected_base_sha="a"*40, operation="commit_files")
    proposal = Proposal("orion", "T1", "gitea_write_intent", "owner/repo",
        args={"branch": intent.branch, "base_sha": intent.expected_base_sha,
              "operation": intent.operation}, requested_network=True)
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
    auth = issue_authorization(proposal, RiskClass.YELLOW, expiry, SECRET, source_revision="a"*40)
    return intent, proposal, auth


class GiteaAuthorizationGateTests(unittest.TestCase):
    def test_matching_grant(self):
        i,p,a = setup()
        self.assertEqual(GiteaAuthorizationGate().grant(i,p,a,SECRET,source_revision="a"*40).intent, i)

    def test_replay_denied(self):
        i,p,a = setup()
        gate = GiteaAuthorizationGate()
        gate.grant(i,p,a,SECRET,source_revision="a"*40)
        with self.assertRaises(ValueError):
            gate.grant(i,p,a,SECRET,source_revision="a"*40)

    def test_stale_revision_denied(self):
        i,p,a = setup()
        with self.assertRaises(ValueError):
            GiteaAuthorizationGate().grant(i,p,a,SECRET,source_revision="b"*40)

    def test_wrong_scope_denied(self):
        i,p,a = setup()
        with self.assertRaises(ValueError):
            GiteaAuthorizationGate().grant(replace(i,task_id="T2"),p,a,SECRET,source_revision="a"*40)

    def test_tampered_args_denied(self):
        i,p,a = setup()
        with self.assertRaises(ValueError):
            GiteaAuthorizationGate().grant(i,replace(p,args={"branch":"main"}),a,SECRET,source_revision="a"*40)

    def test_wrong_signature_denied(self):
        i,p,a = setup()
        with self.assertRaises(ValueError):
            GiteaAuthorizationGate().grant(i,p,replace(a,signature="0"*64),SECRET,source_revision="a"*40)

    def test_green_auth_denied(self):
        i,p,a = setup()
        expiry = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
        green = issue_authorization(p,RiskClass.GREEN,expiry,SECRET,source_revision="a"*40)
        with self.assertRaises(ValueError):
            GiteaAuthorizationGate().grant(i,p,green,SECRET,source_revision="a"*40)

    def test_network_flag_required(self):
        i,p,a = setup()
        with self.assertRaises(ValueError):
            GiteaAuthorizationGate().grant(i,replace(p,requested_network=False),a,SECRET,source_revision="a"*40)


if __name__ == "__main__":
    unittest.main()
