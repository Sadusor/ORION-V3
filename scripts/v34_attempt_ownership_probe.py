from __future__ import annotations

import tempfile
from pathlib import Path

from orion_v3.state import AttemptAuthority, AttemptDenied, OrionStateStore


class Clock:
    def __init__(self, value: float = 1000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


def expect_denied(code: str, fn) -> None:
    try:
        fn()
    except AttemptDenied as exc:
        assert exc.code == code, (exc.code, code)
        return
    raise AssertionError(f"expected denial: {code}")


def main() -> int:
    print("V3_RUN_ID> V3-RUN-019")
    print("ATTEMPT_OWNERSHIP_GATE> START")

    with tempfile.TemporaryDirectory(prefix="orion-v3-attempt-") as temp:
        db_path = Path(temp) / "orion-core.db"
        store = OrionStateStore(db_path)
        store.initialize()
        project = store.create_project("ORION", project_id="orion")
        task = store.create_task(
            project.project_id,
            "Prove durable Attempt ownership",
            task_id="task-attempt",
        )

        clock = Clock()
        tokens = iter(["attempt-token-a", "attempt-token-b", "attempt-token-c"])
        authority = AttemptAuthority(
            store,
            clock=clock,
            token_factory=lambda: next(tokens),
        )
        authority.initialize()
        attempt = authority.create_attempt(task.task_id, attempt_id="attempt-019")
        assert attempt.status == "PENDING"
        print("ATTEMPT_CREATE> PASS")

        first = authority.claim(
            attempt.attempt_id,
            worker_id="worker-a",
            ttl_seconds=10,
        )
        expect_denied(
            "active_attempt_lease",
            lambda: authority.claim(
                attempt.attempt_id,
                worker_id="worker-b",
                ttl_seconds=10,
            ),
        )
        print("SINGLE_ACTIVE_LEASE> PASS")

        expect_denied(
            "missing_attempt_lease",
            lambda: authority.checkpoint(attempt.attempt_id, None, {"phase": "bad"}),
        )
        saved = authority.checkpoint(
            attempt.attempt_id,
            first.token,
            {"phase": "prepared"},
        )
        assert saved.checkpoint_seq == 1
        print("CHECKPOINT_REQUIRES_LEASE> PASS")

        clock.value = first.lease.expires_at
        expect_denied(
            "expired_attempt_lease",
            lambda: authority.checkpoint(
                attempt.attempt_id,
                first.token,
                {"phase": "late"},
            ),
        )
        print("EXPIRED_LEASE_ADVANCE> DENIED")

        second = authority.claim(
            attempt.attempt_id,
            worker_id="worker-b",
            ttl_seconds=20,
        )
        assert second.lease.generation == first.lease.generation + 1
        print("LEASE_RECLAIM_AFTER_EXPIRY> PASS")

        expect_denied(
            "stale_attempt_lease",
            lambda: authority.finish(
                attempt.attempt_id,
                first.token,
                status="SUCCEEDED",
                result={"worker": "worker-a"},
            ),
        )
        print("STALE_LATE_WORKER> DENIED")

        current = authority.checkpoint(
            attempt.attempt_id,
            second.token,
            {"phase": "running", "worker": "worker-b"},
        )
        assert current.checkpoint_seq == 2

        store.close()
        reopened_store = OrionStateStore(db_path)
        reopened_store.initialize()
        reopened = AttemptAuthority(
            reopened_store,
            clock=clock,
            token_factory=lambda: "attempt-token-c",
        )
        reopened.initialize()
        recovered = reopened.get_attempt(attempt.attempt_id)
        assert recovered.status == "RUNNING"
        assert recovered.lease_generation == second.lease.generation
        assert recovered.checkpoint == {"phase": "running", "worker": "worker-b"}
        expect_denied(
            "active_attempt_lease",
            lambda: reopened.claim(
                attempt.attempt_id,
                worker_id="worker-c",
                ttl_seconds=5,
            ),
        )
        print("REOPEN_RECOVERY> PASS")

        stopped = reopened.stop(
            attempt.attempt_id,
            requested_by="owner",
            reason="prove Stop ownership",
        )
        assert stopped.status == "STOPPED"
        assert stopped.lease_revoked_at is not None
        print("STOP_INVALIDATES_OWNERSHIP> PASS")

        expect_denied(
            "stopped_attempt",
            lambda: reopened.checkpoint(
                attempt.attempt_id,
                second.token,
                {"phase": "too-late"},
            ),
        )
        expect_denied(
            "stopped_attempt",
            lambda: reopened.finish(
                attempt.attempt_id,
                second.token,
                status="SUCCEEDED",
                result={"late": True},
            ),
        )
        print("LATE_RESULT_AFTER_STOP> DENIED")

        print("NETWORK_MODEL_EXECUTION_DEPENDENCY> NONE")
        print("ATTEMPT_OWNERSHIP_GATE> PASS")
        print("STATUS> PASS")
        reopened_store.close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
