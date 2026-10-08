from concurrent.futures import ThreadPoolExecutor
from orion_v3.work_loop.contracts import EvidenceRecord, WorkState
from orion_v3.work_loop.vault import ProjectVault


def test_cross_instance_writes_are_serialized(tmp_path):
    a = ProjectVault(tmp_path)
    a.initialize(WorkState("p", "goal", "checkpoint", "task"))
    b = ProjectVault(tmp_path)
    def write(i):
        vault = a if i % 2 == 0 else b
        evidence = EvidenceRecord("p", "task", "hash", "execution", "indeterminate", "sim", "rev", str(i))
        vault.record_verified_result(evidence, next_action="wait")
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(write, range(8)))
    journal = a.journal_path.read_text(encoding="utf-8")
    assert sum("source=sim@rev" in line for line in journal.splitlines()) == 8
    assert a.load().blocked


def test_stop_guard_denies_vault_commit(tmp_path):
    from orion_v3.work_loop.vault import VaultError
    import pytest
    vault = ProjectVault(tmp_path)
    vault.initialize(WorkState("p", "goal", "checkpoint", "task"))
    e = EvidenceRecord("p", "task", "hash", "execution", "indeterminate", "sim", "rev")
    with pytest.raises(VaultError):
        vault.record_verified_result(e, next_action="wait", commit_guard=lambda: False)
    assert vault.load().last_verified_result == "none"
    assert not vault.pending_path.exists()
