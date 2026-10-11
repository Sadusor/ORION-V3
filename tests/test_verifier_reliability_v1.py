import sys
import unittest
from pathlib import Path
from unittest.mock import Mock
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "src" / "orion_v3"))
from modules.verifier_reliability_v1 import VerifierReliabilityV1
from modules.verifier_preflight import VerifierError

GOOD={"preflight":"pass","preflight_reason":"","quality_state":"pass","quality_reason":"","unsupported_claims":[],"missing_evidence":[],"needs_escalation":False}

class VerifierReliabilityTests(unittest.TestCase):
    def test_success_one_call(self):
        wrapped=Mock();wrapped.verify.return_value=GOOD
        self.assertEqual(VerifierReliabilityV1(wrapped).verify("hi","hello","qwen"),GOOD)
        self.assertEqual(wrapped.verify.call_count,1)
    def test_malformed_json_retries_exactly_once(self):
        wrapped=Mock();wrapped.verify.side_effect=[VerifierError("Local verifier returned malformed structured JSON."),GOOD]
        self.assertEqual(VerifierReliabilityV1(wrapped).verify("hi","hello","qwen"),GOOD)
        self.assertEqual(wrapped.verify.call_count,2)
    def test_schema_mismatch_retries_once(self):
        wrapped=Mock();wrapped.verify.side_effect=[VerifierError("Local verifier output did not match the required schema."),GOOD]
        self.assertEqual(VerifierReliabilityV1(wrapped).verify("hi","hello","qwen"),GOOD)
    def test_persistent_malformed_does_not_pass(self):
        wrapped=Mock();wrapped.verify.side_effect=VerifierError("Local verifier returned malformed structured JSON.")
        with self.assertRaises(VerifierError):
            VerifierReliabilityV1(wrapped).verify("hi","hello","qwen")
        self.assertEqual(wrapped.verify.call_count,2)
    def test_transport_error_never_retried(self):
        wrapped=Mock();wrapped.verify.side_effect=VerifierError("Local verifier request failed")
        with self.assertRaises(VerifierError):
            VerifierReliabilityV1(wrapped).verify("hi","hello","qwen")
        self.assertEqual(wrapped.verify.call_count,1)
    def test_explicit_semantic_block_never_retried(self):
        wrapped=Mock();wrapped.verify.return_value=dict(GOOD, quality_state="blocked")
        result=VerifierReliabilityV1(wrapped).verify("hi","hello","qwen")
        self.assertEqual(result["quality_state"],"blocked")
        self.assertEqual(wrapped.verify.call_count,1)

if __name__=='__main__':unittest.main()
