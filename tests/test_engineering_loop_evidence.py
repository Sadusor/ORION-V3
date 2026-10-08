"""Contract tests only: no external GitHub, PowerShell or live execution."""
import pytest
from orion_v3.engineering_loop import assess_cycle, EvidenceContractError

O = "a" * 40
T = "b" * 40
H = "c" * 40
S = "session_123"

def evidence(result="PASS"):
    return {"schema": "thehands.github-evidence.v1", "evidence_id": "thehands-" + S,
            "hand_id": "powershell-1", "source_commit": T, "hand_tree_sha": H,
            "result": result, "output_tail": "script exited"}

def check(e, **overrides):
    args = dict(session_id=S, expected_orion_revision=O, expected_thehands_commit=T,
                expected_hand_tree=H, expected_hand_id="powershell-1", published=e)
    args.update(overrides)
    return assess_cycle(**args)

def test_script_pass_does_not_prove_orion_pass():
    assert check(evidence()).product_verdict == "UNVERIFIED"
    assert check(evidence(), observed_orion_revision=O).product_verdict == "UNVERIFIED"

def test_matching_revision_and_independent_acceptance():
    x = check(evidence(), observed_orion_revision=O, acceptance_passed=True)
    assert x.product_verdict == "PASS" and x.next_action == "document_and_freeze"

def test_wrong_orion_revision_blocks_pass():
    assert check(evidence(), observed_orion_revision="d"*40, acceptance_passed=True).product_verdict == "UNVERIFIED"

def test_failed_and_stopped_run_never_pass():
    for result in ("FAIL", "STOPPED"):
        assert check(evidence(result), observed_orion_revision=O, acceptance_passed=True).product_verdict == result

@pytest.mark.parametrize("field,value", [("source_commit", "d"*40), ("hand_tree_sha", "d"*40),
                                           ("hand_id", "powershell-2"), ("evidence_id", "thehands-other"),
                                           ("schema", "wrong"), ("result", "MAYBE")])
def test_mismatched_published_evidence_is_rejected(field, value):
    e = evidence(); e[field] = value
    with pytest.raises(EvidenceContractError): check(e)
