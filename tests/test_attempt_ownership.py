from __future__ import annotations

from pathlib import Path

import pytest

from orion_v3.state import (
    AttemptAuthority,
    AttemptDenied,
    OrionStateStore,
)


class Clock:
    def __init__(self, value: float = 1000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


def build(tmp_path: Path):
    store = OrionStateStore(tmp_path / "core.db")
    store.initialize()
    project = store.create_project("ORION", project_id="orion")
    task = store.create_task(project.project_id, "bounded coding task", task_id="task-1")
    clock = Clock()
    tokens = iter(["lease-a", "lease-b", "lease-c", "lease-d"])
    attempts = AttemptAuthority(
        store,
        clock=clock,
        token_factory=lambda: next(tokens),
    )
    attempts.initialize()
    attempt = attempts.create_attempt(task.task_id, attempt_id="attempt-1")
    return store, clock, attempts, attempt


def denied(code: str, fn) -> None:
    with pytest.raises(AttemptDenied) as exc:
        fn()
    assert exc.value.code == code


def test_only_one_active_lease_can_own_attempt(tmp_path):
    _, _, attempts, attempt = build(tmp_path)
    first = attempts.claim(attempt.attempt_id, worker_id="worker-a", ttl_seconds=30)

    denied(
        "active_attempt_lease",
        lambda: attempts.claim(attempt.attempt_id, worker_id="worker-b", ttl_seconds=30),
    )
    assert first.lease.generation == 1


def test_checkpoint_requires_current_matching_lease(tmp_path):
    _, _, attempts, attempt = build(tmp_path)
    issued = attempts.claim(attempt.attempt_id, worker_id="worker-a", ttl_seconds=30)

    denied(
        "missing_attempt_lease",
        lambda: attempts.checkpoint(attempt.attempt_id, None, {"step": 1}),
    )
    denied(
        "stale_attempt_lease",
        lambda: attempts.checkpoint(attempt.attempt_id, "forged", {"step": 1}),
    )

    saved = attempts.checkpoint(attempt.attempt_id, issued.token, {"step": 1})
    assert saved.checkpoint_seq == 1
    assert saved.checkpoint == {"step": 1}


def test_expired_lease_cannot_advance_and_new_generation_fences_old_worker(tmp_path):
    _, clock, attempts, attempt = build(tmp_path)
    first = attempts.claim(attempt.attempt_id, worker_id="worker-a", ttl_seconds=10)
    clock.value = first.lease.expires_at

    denied(
        "expired_attempt_lease",
        lambda: attempts.checkpoint(attempt.attempt_id, first.token, {"late": True}),
    )

    second = attempts.claim(attempt.attempt_id, worker_id="worker-b", ttl_seconds=10)
    assert second.lease.generation == 2
    assert first.token != second.token
    denied(
        "stale_attempt_lease",
        lambda: attempts.checkpoint(attempt.attempt_id, first.token, {"late": True}),
    )

    current = attempts.checkpoint(attempt.attempt_id, second.token, {"owner": "worker-b"})
    assert current.lease_generation == 2
    assert current.checkpoint == {"owner": "worker-b"}


def test_stop_revokes_execution_before_checkpoint_or_result(tmp_path):
    _, _, attempts, attempt = build(tmp_path)
    issued = attempts.claim(attempt.attempt_id, worker_id="worker-a", ttl_seconds=30)
    stopped = attempts.stop(
        attempt.attempt_id,
        requested_by="owner",
        reason="owner requested stop",
    )

    assert stopped.status == "STOPPED"
    assert stopped.lease_revoked_at is not None
    denied(
        "stopped_attempt",
        lambda: attempts.checkpoint(attempt.attempt_id, issued.token, {"late": True}),
    )
    denied(
        "stopped_attempt",
        lambda: attempts.finish(
            attempt.attempt_id,
            issued.token,
            status="SUCCEEDED",
            result={"late": True},
        ),
    )


def test_late_result_from_replaced_worker_cannot_finish_attempt(tmp_path):
    _, clock, attempts, attempt = build(tmp_path)
    first = attempts.claim(attempt.attempt_id, worker_id="worker-a", ttl_seconds=5)
    clock.value = first.lease.expires_at
    second = attempts.claim(attempt.attempt_id, worker_id="worker-b", ttl_seconds=20)

    denied(
        "stale_attempt_lease",
        lambda: attempts.finish(
            attempt.attempt_id,
            first.token,
            status="SUCCEEDED",
            result={"worker": "a"},
        ),
    )
    finished = attempts.finish(
        attempt.attempt_id,
        second.token,
        status="SUCCEEDED",
        result={"worker": "b"},
    )
    assert finished.status == "SUCCEEDED"
    assert finished.result == {"worker": "b"}


def test_restart_preserves_attempt_checkpoint_and_current_ownership(tmp_path):
    store, clock, attempts, attempt = build(tmp_path)
    issued = attempts.claim(attempt.attempt_id, worker_id="worker-a", ttl_seconds=50)
    attempts.checkpoint(attempt.attempt_id, issued.token, {"phase": "prepared"})
    db_path = store.path
    store.close()

    reopened_store = OrionStateStore(db_path)
    reopened_store.initialize()
    reopened = AttemptAuthority(
        reopened_store,
        clock=clock,
        token_factory=lambda: "lease-new",
    )
    reopened.initialize()

    recovered = reopened.get_attempt(attempt.attempt_id)
    assert recovered.status == "RUNNING"
    assert recovered.lease_generation == 1
    assert recovered.lease_worker_id == "worker-a"
    assert recovered.checkpoint == {"phase": "prepared"}

    denied(
        "active_attempt_lease",
        lambda: reopened.claim(attempt.attempt_id, worker_id="worker-b", ttl_seconds=10),
    )

    checkpoint = reopened.checkpoint(
        attempt.attempt_id,
        issued.token,
        {"phase": "resumed"},
    )
    assert checkpoint.checkpoint_seq == 2
    assert checkpoint.checkpoint == {"phase": "resumed"}


def test_generation_fences_even_if_token_factory_repeats_raw_token(tmp_path):
    store = OrionStateStore(tmp_path / "repeat.db")
    store.initialize()
    project = store.create_project("ORION", project_id="orion-repeat")
    task = store.create_task(project.project_id, "repeat token test", task_id="task-repeat")
    clock = Clock()
    attempts = AttemptAuthority(
        store,
        clock=clock,
        token_factory=lambda: "same-raw-token",
    )
    attempts.initialize()
    attempt = attempts.create_attempt(task.task_id, attempt_id="attempt-repeat")

    first = attempts.claim(attempt.attempt_id, worker_id="worker-a", ttl_seconds=5)
    clock.value = first.lease.expires_at
    second = attempts.claim(attempt.attempt_id, worker_id="worker-b", ttl_seconds=10)

    assert second.lease.generation == 2
    denied(
        "stale_attempt_lease",
        lambda: attempts.checkpoint(
            attempt.attempt_id,
            first.token,
            {"worker": "a"},
        ),
    )
