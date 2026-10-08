"""Two-process M4 recovery proof: persist authenticated FAIL, restart, reject forged PASS.

This is not a real Qwen or execution test. The independent PASS gate is intentionally
closed until a real verifier is wired.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

from orion_v3.work_loop.contracts import EvidenceRecord, WorkState
from orion_v3.work_loop.engine import WorkLoopEngine
from orion_v3.work_loop.qwen_proposal_adapter import parse_qwen_proposal
from orion_v3.work_loop.vault import ProjectVault

phase, base_arg = sys.argv[1:]
base = Path(base_arg).resolve()
vault = ProjectVault(base / "vault")
workspace = base / "workspace"
payload = dict(project_id="m4-recovery", task_id="task-1", operation="filesystem.write",
               workspace=str(workspace), args={"path": str(workspace / "fixture.txt"), "content": "repaired"},
               requested_network=False, requested_install=False, requested_system_change=False)
if phase == "fail":
    workspace.mkdir(parents=True, exist_ok=True)
    vault.initialize(WorkState("m4-recovery", "repair a deliberate failure", "before-fail", "task-1"))
    engine = WorkLoopEngine(vault)
    proposal = parse_qwen_proposal(json.dumps(payload), engine)
    evidence = EvidenceRecord(proposal.project_id, proposal.task_id, proposal.proposal_hash,
                              "test", "fail", "trusted-test-fixture", "m4-recovery-v1",
                              "deliberate deterministic failing test")
    outcome = engine.apply_evidence(proposal, evidence, required_type="test",
                                    expected_source_revision="m4-recovery-v1",
                                    next_action_on_pass="done", next_action_on_fail="repair required")
    assert outcome.state_updated and vault.load().last_verified_result == "test:fail"
    print("M4_RECOVERY> AUTHENTICATED_FAIL_PERSISTED_PASS")
elif phase == "restart":
    engine = WorkLoopEngine(ProjectVault(base / "vault"))
    state = engine.vault.load()
    assert state.last_verified_result == "test:fail" and state.blocked and state.next_action == "repair required"
    print("M4_RECOVERY> FRESH_PROCESS_RECOVERED_FAIL_PASS")
    proposal = parse_qwen_proposal(json.dumps(payload), engine)
    assert proposal.args["content"] == "repaired"
    print("M4_RECOVERY> FRESH_ADAPTER_REPAIR_PROPOSAL_ACCEPTED_PASS")
    forged = EvidenceRecord(proposal.project_id, proposal.task_id, proposal.proposal_hash,
                            "test", "pass", "untrusted-executor", "m4-recovery-v1", "self-claimed PASS")
    outcome = engine.apply_evidence(proposal, forged, required_type="test",
                                    expected_source_revision="m4-recovery-v1",
                                    next_action_on_pass="done", next_action_on_fail="repair required",
                                    trusted_verifier_pass=True)
    assert not outcome.state_updated and engine.vault.load().last_verified_result == "test:fail"
    print("M4_RECOVERY> UNVERIFIED_PASS_DENIED_VAULT_FAIL_PRESERVED_PASS")
    from orion_v3.work_loop.m4_fixture_verifier import verify_fixture_and_record
    target = workspace / "fixture.txt"
    target.write_bytes(b"wrong")
    try:
        verify_fixture_and_record(engine, proposal, source_revision="m4-recovery-v1",
                                  stop_requested=lambda: False)
    except ValueError:
        pass
    else:
        raise AssertionError("wrong bytes were accepted")
    assert engine.vault.load().last_verified_result == "test:fail"
    print("M4_RECOVERY> WRONG_BYTES_REJECTED_FAIL_PRESERVED_PASS")
    target.write_bytes(b"repaired")
    try:
        verify_fixture_and_record(engine, proposal, source_revision="m4-recovery-v1",
                                  stop_requested=lambda: True)
    except RuntimeError:
        pass
    else:
        raise AssertionError("STOP failed to deny PASS")
    assert engine.vault.load().last_verified_result == "test:fail"
    print("M4_RECOVERY> STOP_BLOCKED_VERIFIER_PASS")
    verify_fixture_and_record(engine, proposal, source_revision="m4-recovery-v1",
                              stop_requested=lambda: False)
    assert engine.vault.load().last_verified_result == "test:pass"
    assert not engine.vault.load().blocked
    assert "TEST PASS" in engine.vault.journal_path.read_text(encoding="utf-8")
    print("M4_RECOVERY> INDEPENDENT_FIXTURE_BYTES_VERIFIED_AND_VAULT_PASS")
    print("M4_RECOVERY> REAL_QWEN_AND_NATIVE_REPAIR_EXECUTION_NOT_YET_QUALIFIED")
else:
    raise SystemExit("invalid phase")
