import unittest
from orion_v3.work_loop.generated_execution_boundary_gate_v1 import BoundaryEvidence, authorize_generated_execution

def evidence(**kwargs):
    d = dict(backend="windows-appcontainer", filesystem_denial=True,
        network_denial=True, process_tree_stop=True, timeout_enforced=True,
        evidence_authenticated=True, measured_on_host=True)
    d.update(kwargs)
    return BoundaryEvidence(**d)

class GeneratedExecutionBoundaryGateTests(unittest.TestCase):
    def test_missing(self):
        self.assertEqual(authorize_generated_execution(None)["reason"], "MISSING_BOUNDARY_EVIDENCE")
    def test_backend(self):
        self.assertEqual(authorize_generated_execution(evidence(backend="python-I"), owner_approved=True)["reason"], "UNQUALIFIED_BACKEND")
    def test_filesystem(self):
        self.assertEqual(authorize_generated_execution(evidence(filesystem_denial=False), owner_approved=True)["reason"], "BOUNDARY_NOT_PROVEN")
    def test_network(self):
        self.assertEqual(authorize_generated_execution(evidence(network_denial=False), owner_approved=True)["reason"], "BOUNDARY_NOT_PROVEN")
    def test_stop(self):
        self.assertEqual(authorize_generated_execution(evidence(process_tree_stop=False), owner_approved=True)["reason"], "BOUNDARY_NOT_PROVEN")
    def test_timeout(self):
        self.assertEqual(authorize_generated_execution(evidence(timeout_enforced=False), owner_approved=True)["reason"], "BOUNDARY_NOT_PROVEN")
    def test_authentication(self):
        self.assertEqual(authorize_generated_execution(evidence(evidence_authenticated=False), owner_approved=True)["reason"], "BOUNDARY_NOT_PROVEN")
    def test_host_measurement(self):
        self.assertEqual(authorize_generated_execution(evidence(measured_on_host=False), owner_approved=True)["reason"], "BOUNDARY_NOT_PROVEN")
    def test_owner(self):
        self.assertEqual(authorize_generated_execution(evidence())["reason"], "OWNER_APPROVAL_REQUIRED")
    def test_self_declared_all_true_still_denied(self):
        self.assertEqual(authorize_generated_execution(evidence(), owner_approved=True),
            {"authorized": False, "reason": "TRUSTED_ATTESTATION_VERIFIER_NOT_IMPLEMENTED"})
    def test_non_boolean_rejected(self):
        self.assertEqual(authorize_generated_execution(evidence(network_denial=1), owner_approved=True)["reason"], "BOUNDARY_NOT_PROVEN")

if __name__ == "__main__":
    unittest.main()
