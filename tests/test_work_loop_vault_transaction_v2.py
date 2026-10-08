"""V2 Vault transaction recovery: exact markers, legacy compatibility, fail closed."""
from dataclasses import asdict, replace

import pytest

from orion_v3.work_loop.contracts import EvidenceRecord, WorkState
from orion_v3.work_loop.vault import ProjectVault
from orion_v3.work_loop.vault_transaction import (
    journal_contains, journal_entry, new_pending, parse_pending,
)


@pytest.fixture
def vault(tmp_path):
    v = ProjectVault(tmp_path / "vault")
    v.initialize(WorkState("p", "goal", "checkpoint", "t"))
    return v


def test_real_commit_writes_unique_transaction_marker(vault):
    evidence = EvidenceRecord("p", "t", "a" * 64, "execution", "fail", "hand", "rev")
    vault.record_verified_result(evidence, next_action="stop", blocked=True)
    journal = vault.journal_path.read_text(encoding="utf-8")
    assert "txid=" in journal
    assert not vault.pending_path.exists()


def test_pending_v2_recovery_exactly_once(vault):
    updated = replace(vault.load(), last_verified_result="execution:fail", blocked=True)
    pending = new_pending("EVENT_REPLAY", asdict(updated))
    vault._write_pending(pending)
    assert ProjectVault(vault.root).load() == updated
    first = vault.journal_path.read_bytes()
    assert first.count(pending["txid"].encode()) == 1
    assert ProjectVault(vault.root).load() == updated
    assert vault.journal_path.read_bytes() == first


def test_similar_journal_text_does_not_suppress_recovery(vault):
    updated = replace(vault.load(), blocked=True)
    pending = new_pending("EVENT_SUBSTRING", asdict(updated))
    vault.append_journal("OTHER_EVENT EVENT_SUBSTRING")
    vault._write_pending(pending)
    vault.load()
    journal = vault.journal_path.read_text(encoding="utf-8")
    assert journal.count("EVENT_SUBSTRING") == 2
    assert journal.count(pending["txid"]) == 1


def test_exact_id_dedup_after_journal_written(vault):
    updated = replace(vault.load(), blocked=True)
    pending = new_pending("EXACT_EVENT", asdict(updated))
    vault._write_pending(pending)
    vault._write_state(updated)
    vault.append_journal(journal_entry(pending["entry"], pending["txid"]))
    vault.load()
    assert vault.journal_path.read_text(encoding="utf-8").count(pending["txid"]) == 1


@pytest.mark.parametrize("field,value", [
    ("version", 3), ("phase", "unverified"), ("txid", "bad"),
    ("entry", ""), ("state", None),
])
def test_invalid_pending_v2_rejected(vault, field, value):
    pending = new_pending("EVENT", asdict(vault.load()))
    pending[field] = value
    vault._write_pending(pending)
    before = (vault.state_path.read_bytes(), vault.journal_path.read_bytes())
    with pytest.raises(ValueError):
        ProjectVault(vault.root).load()
    assert (vault.state_path.read_bytes(), vault.journal_path.read_bytes()) == before


def test_legacy_v1_pending_still_recovers(vault):
    updated = replace(vault.load(), blocked=True)
    vault._write_pending({"entry": "LEGACY_EVENT", "state": asdict(updated)})
    assert ProjectVault(vault.root).load() == updated
    assert "LEGACY_EVENT" in vault.journal_path.read_text(encoding="utf-8")


def test_journal_marker_matches_only_complete_line_suffix():
    txid = "a" * 32
    assert journal_contains("- time — EVENT txid=" + txid + "\n", "EVENT", txid)
    assert not journal_contains("- time — EVENT txid=" + txid + "extra\n", "EVENT", txid)
    assert not journal_contains("- time — EVENT txid=" + "b" * 32 + "\n", "EVENT", txid)
