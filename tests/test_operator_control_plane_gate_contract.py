from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def gate_source() -> str:
    return (
        ROOT / "scripts" / "v36_operator_control_plane_gate.py"
    ).read_text(encoding="utf-8")


def test_run044_proves_exact_action_freeze_and_single_use():
    text = gate_source()
    assert "EXACT_ACTION_FREEZE> PASS" in text
    assert "EXACT_APPROVED_ACTION_RESUME> PASS" in text
    assert "MODEL_REWRITE_ON_RESUME> NONE" in text
    assert "SINGLE_USE_APPROVAL> PASS" in text
    assert 'expect_denied(\n            "stale_approval"' in text


def test_run044_proves_idempotent_approval_and_human_decision():
    text = gate_source()
    assert "DUPLICATE_APPROVAL_REQUEST_IDEMPOTENT> PASS" in text
    assert "DUPLICATE_HUMAN_APPROVE_IDEMPOTENT> PASS" in text


def test_run044_proves_wrong_task_rejection_and_tamper_guard():
    text = gate_source()
    assert 'expect_denied(\n            "wrong_task"' in text
    assert "FROZEN_ACTION_TAMPER_GUARD> PASS" in text
    assert '"approval_tamper_detected"' in text


def test_run044_proves_rejection_and_restart_staleness():
    text = gate_source()
    assert "REJECTED_ACTION_EXECUTION> DENIED" in text
    assert "RESTART_PERSISTENCE> PASS" in text
    assert "STALE_REPLAY_AFTER_RESTART> DENIED" in text


def test_run044_proves_cloud_queue_without_live_provider():
    text = gate_source()
    assert "CLOUD_QUEUE_IDEMPOTENT> PASS" in text
    assert "CLOUD_QUEUE_EVENT_EXCHANGE> PASS" in text
    assert "LIVE_CLOUD_PROVIDER_CALL> NONE" in text


def test_run044_has_no_model_network_or_execution_dependency():
    text = gate_source()
    assert "MODEL_DEPENDENCY> NONE" in text
    assert "NETWORK_DEPENDENCY> NONE" in text
    assert "EXECUTION_SIDE_EFFECT> NONE" in text
