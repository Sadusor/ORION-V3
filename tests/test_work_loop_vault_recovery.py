import json
from orion_v3.work_loop.contracts import WorkState, EvidenceRecord
from orion_v3.work_loop.vault import ProjectVault


def test_vault_recovers_pending_state_and_journal(tmp_path):
    vault = ProjectVault(tmp_path)
    vault.initialize(WorkState("p", "goal", "checkpoint", "t"))
    updated = WorkState("p", "goal", "checkpoint", "t",
                        last_verified_result="execution:indeterminate",
                        next_action="wait", blocked=True)
    from dataclasses import asdict
    vault.pending_path.write_text(json.dumps({"state": asdict(updated),
        "entry": "RECOVERY TEST UNIQUE"}), encoding="utf-8")
    assert vault.load().next_action == "wait"
    assert not vault.pending_path.exists()
    assert vault.journal_path.read_text(encoding="utf-8").count("RECOVERY TEST UNIQUE") == 1
    assert vault.load().next_action == "wait"
    assert vault.journal_path.read_text(encoding="utf-8").count("RECOVERY TEST UNIQUE") == 1


def test_vault_serialized_transition(tmp_path):
    vault = ProjectVault(tmp_path)
    vault.initialize(WorkState("p", "goal", "checkpoint", "t"))
    e = EvidenceRecord("p", "t", "hash", "execution", "indeterminate", "sim", "rev")
    vault.record_verified_result(e, next_action="wait")
    assert vault.load().blocked is True
    assert not vault.pending_path.exists()
