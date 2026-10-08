import pytest

from orion_v3.work_loop.contracts import WorkState
from orion_v3.work_loop.model_cycle_simulation import simulate_model_cycle
from orion_v3.work_loop.model_proposal import ProposalParseError
from orion_v3.work_loop.vault import ProjectVault


class Stop:
    def __init__(self, active=False):
        self.active = active

    def stop_requested(self):
        return self.active


def setup(tmp_path):
    vault = ProjectVault(tmp_path / "work")
    vault.initialize(WorkState(project_id="demo", objective="prove simulation",
                               checkpoint="start", current_task="inspect"))
    return vault


def cycle(vault, text, stop=None):
    return simulate_model_cycle(text, vault=vault, stop=stop or Stop(),
                                secret=b"test-only", source_revision="fixture")


def test_green_simulation_records_indeterminate_not_pass(tmp_path):
    vault = setup(tmp_path)
    result = cycle(vault, '{"operation":"git.status"}')
    assert result.outcome.status == "dry_run"
    assert result.outcome.evidence.verdict == "indeterminate"
    assert result.state.last_verified_result == "execution:indeterminate"
    assert result.state.blocked is True
    assert "INDETERMINATE" in vault.journal_path.read_text(encoding="utf-8")
    assert not list(vault.repo_path.iterdir())


def test_yellow_never_reaches_hand_or_changes_vault(tmp_path):
    vault = setup(tmp_path)
    result = cycle(vault, '{"operation":"git.status","requested_network":true}')
    assert result.outcome.status == "awaiting_owner"
    assert result.state.last_verified_result == "none"


def test_red_never_reaches_hand_or_changes_vault(tmp_path):
    vault = setup(tmp_path)
    result = cycle(vault, '{"operation":"system.shutdown"}')
    assert result.outcome.status == "denied"
    assert result.state.last_verified_result == "none"


def test_stop_blocks_before_execution(tmp_path):
    vault = setup(tmp_path)
    result = cycle(vault, '{"operation":"git.status"}', Stop(True))
    assert result.outcome.status == "stopped"
    assert result.state.last_verified_result == "none"


def test_model_cannot_supply_scope_or_approval(tmp_path):
    vault = setup(tmp_path)
    with pytest.raises(ProposalParseError):
        cycle(vault, '{"operation":"git.status","project_id":"other","approved":true}')
    assert vault.load().last_verified_result == "none"


def test_model_can_propose_write_but_simulation_does_not_write(tmp_path):
    vault = setup(tmp_path)
    target = vault.repo_path / "hello.txt"
    import json
    text = json.dumps({"operation":"filesystem.write","args":{"path":str(target),"content":"hello"}})
    result = cycle(vault, text)
    assert result.outcome.status == "dry_run"
    assert not target.exists()
    assert result.state.last_verified_result == "execution:indeterminate"
