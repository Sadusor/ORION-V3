from __future__ import annotations

import hashlib
import subprocess
import tempfile
from pathlib import Path

from orion_v3.coding_factory import (
    ArtifactStore,
    CodingFactoryBlackboard,
    DecisionVerdict,
    ExecutionDenied,
    FileOperation,
    ReviewVerdict,
    WorkPackageExecutor,
    WorkPackageFactory,
)
from orion_v3.state import (
    AttemptAuthority,
    AttemptDenied,
    LocalEventExchange,
    OrionStateStore,
)


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip())
    return proc.stdout.strip()


def accepted_package(
    *,
    store,
    attempts,
    board,
    factory,
    project_id: str,
    task_id: str,
    attempt_id: str,
    base_sha: str,
    relative_path: str,
    payload: str,
    verifier_sha: str,
    worker_id: str,
):
    attempt = attempts.create_attempt(task_id, attempt_id=attempt_id)
    artifact = factory.file_artifact(
        relative_path,
        payload,
        operation=FileOperation.CREATE,
    )
    package = factory.create(
        project_id=project_id,
        task_id=task_id,
        attempt_id=attempt.attempt_id,
        base_sha=base_sha,
        coder_provider="fixture",
        coder_model="deterministic",
        prompt_text="bounded V3-RUN-020 fixture",
        response_text="immutable WorkPackage candidate",
        artifacts=[artifact],
        allowed_paths=["scratch"],
        forbidden_paths=["scratch/forbidden"],
        verifier_spec={
            "kind": "file_sha256",
            "path": relative_path,
            "sha256": verifier_sha,
        },
    )
    loaded = factory.load(package.manifest_artifact_id)
    assert loaded.package_sha256 == package.package_sha256
    proposal = board.submit_candidate(package)
    review = board.review_candidate(
        package,
        proposal.event_id,
        reviewer_provider="fixture",
        reviewer_model="reviewer",
        verdict=ReviewVerdict.ACCEPTABLE,
        findings=["bounded exact-SHA fixture"],
    )
    decision = board.decide_candidate(
        package,
        review.event_id,
        verdict=DecisionVerdict.ACCEPT_CANDIDATE,
        decided_by="policy",
    )
    issued = attempts.claim(
        attempt.attempt_id,
        worker_id=worker_id,
        ttl_seconds=60,
    )
    action = board.authorize_execution(
        package,
        decision.event_id,
        lease=issued.lease,
        authorized_by="policy",
    )
    return attempt, package, issued, action


def main() -> int:
    print("V3_RUN_ID> V3-RUN-020")
    print("WORKPACKAGE_EXECUTION_ENVELOPE_GATE> START")

    repo_root = Path(__file__).resolve().parents[1]
    base_sha = git(repo_root, "rev-parse", "HEAD")
    if len(base_sha) != 40:
        raise AssertionError("HEAD is not exact Git SHA")
    if git(repo_root, "status", "--porcelain=v1", "--untracked-files=no"):
        raise AssertionError("source checkout has tracked changes")
    print("SOURCE_EXACT_SHA_CLEAN> PASS")

    with tempfile.TemporaryDirectory(prefix="orion-v3-exec-envelope-") as temp:
        root = Path(temp)
        store = OrionStateStore(root / "core.db")
        store.initialize()
        project = store.create_project("ORION", project_id="orion")
        task = store.create_task(
            project.project_id,
            "Prove exact-SHA WorkPackage execution envelope",
            task_id="task-run-020",
        )
        attempts = AttemptAuthority(
            store,
            token_factory=iter(
                ["token-pass", "token-stop", "token-fail"]
            ).__next__,
        )
        attempts.initialize()
        artifacts = ArtifactStore(root / "artifacts")
        factory = WorkPackageFactory(artifacts)
        board = CodingFactoryBlackboard(store, LocalEventExchange(store))
        executor = WorkPackageExecutor(
            store=store,
            attempts=attempts,
            factory=factory,
            source_repo=repo_root,
            worktree_root=root / "worktrees",
        )

        payload = "V3-RUN-020 harmless isolated file\n"
        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        attempt, package, issued, action = accepted_package(
            store=store,
            attempts=attempts,
            board=board,
            factory=factory,
            project_id=project.project_id,
            task_id=task.task_id,
            attempt_id="attempt-pass",
            base_sha=base_sha,
            relative_path="scratch/v3_run_020_probe.txt",
            payload=payload,
            verifier_sha=expected,
            worker_id="worker-pass",
        )
        print("IMMUTABLE_PACKAGE_RELOAD> PASS")
        assert action.payload["body"]["lease_generation"] == issued.lease.generation
        assert action.payload["body"]["execution_authority"] is True
        print("LEASE_BOUND_EXECUTION_ACTION> PASS")

        evidence = executor.run(
            manifest_artifact_id=package.manifest_artifact_id,
            expected_package_sha256=package.package_sha256,
            action_event_id=action.event_id,
            lease_token=issued.token,
        )
        assert evidence.base_sha == base_sha
        assert evidence.changed_paths == ("scratch/v3_run_020_probe.txt",)
        assert len(evidence.diff_sha256) == 64
        assert len(evidence.result_tree_sha) == 40
        assert evidence.verifier["status"] == "PASS"
        assert attempts.get_attempt(attempt.attempt_id).status == "SUCCEEDED"
        print("EXACT_SHA_WORKTREE> PASS")
        print("HARMLESS_FILE_APPLY> PASS")
        print("ACTUAL_CHANGED_PATHS> PASS")
        print("DIFF_HASH_TREE_EVIDENCE> PASS")
        print("DETERMINISTIC_VERIFIER> PASS")

        assert not any((root / "worktrees").iterdir())
        assert git(repo_root, "rev-parse", "HEAD") == base_sha
        assert git(repo_root, "status", "--porcelain=v1", "--untracked-files=no") == ""
        print("PASS_CLEANUP> PASS")

        forbidden_commands = {"push", "merge", "commit"}
        assert not forbidden_commands.intersection(evidence.git_subcommands)
        print("PUSH_MERGE_COMMIT> NONE")

        stop_payload = "must never be applied after Stop\n"
        stop_hash = hashlib.sha256(stop_payload.encode("utf-8")).hexdigest()
        stop_attempt, stop_package, stop_issued, stop_action = accepted_package(
            store=store,
            attempts=attempts,
            board=board,
            factory=factory,
            project_id=project.project_id,
            task_id=task.task_id,
            attempt_id="attempt-stop",
            base_sha=base_sha,
            relative_path="scratch/v3_run_020_stop.txt",
            payload=stop_payload,
            verifier_sha=stop_hash,
            worker_id="worker-stop",
        )
        prepared = executor.prepare(
            manifest_artifact_id=stop_package.manifest_artifact_id,
            expected_package_sha256=stop_package.package_sha256,
            action_event_id=stop_action.event_id,
            lease_token=stop_issued.token,
        )
        assert prepared.worktree.exists()
        attempts.stop(
            stop_attempt.attempt_id,
            requested_by="owner",
            reason="V3-RUN-020 stop cleanup probe",
        )
        try:
            executor.continue_execution(prepared, lease_token=stop_issued.token)
        except AttemptDenied as exc:
            assert exc.code == "stopped_attempt"
        else:
            raise AssertionError("stopped Attempt unexpectedly executed")
        assert not prepared.worktree.exists()
        assert attempts.get_attempt(stop_attempt.attempt_id).status == "STOPPED"
        print("STOP_BEFORE_EFFECT> DENIED")
        print("STOP_CLEANUP> PASS")

        fail_payload = "verifier should reject this fixture\n"
        fail_attempt, fail_package, fail_issued, fail_action = accepted_package(
            store=store,
            attempts=attempts,
            board=board,
            factory=factory,
            project_id=project.project_id,
            task_id=task.task_id,
            attempt_id="attempt-fail",
            base_sha=base_sha,
            relative_path="scratch/v3_run_020_fail.txt",
            payload=fail_payload,
            verifier_sha="0" * 64,
            worker_id="worker-fail",
        )
        try:
            executor.run(
                manifest_artifact_id=fail_package.manifest_artifact_id,
                expected_package_sha256=fail_package.package_sha256,
                action_event_id=fail_action.event_id,
                lease_token=fail_issued.token,
            )
        except ExecutionDenied as exc:
            assert exc.code == "verifier_failed"
        else:
            raise AssertionError("bad verifier unexpectedly passed")
        assert attempts.get_attempt(fail_attempt.attempt_id).status == "FAILED"
        assert not any((root / "worktrees").iterdir())
        print("VERIFIER_FAILURE> DENIED")
        print("FAIL_CLEANUP> PASS")

        chain = store.list_task_events(project.project_id, task.task_id, limit=50)
        pass_chain = [
            event.event_type.value
            for event in chain
            if event.attempt_id == "attempt-pass"
        ]
        assert pass_chain == [
            "PROPOSAL",
            "REVIEW",
            "DECISION",
            "ACTION",
            "EVIDENCE",
            "RESULT",
        ]
        print("ACTION_EVIDENCE_RESULT_CHAIN> PASS")
        print("NETWORK_MODEL_DEPENDENCY> NONE")
        print("WORKPACKAGE_EXECUTION_ENVELOPE_GATE> PASS")
        print("STATUS> PASS")
        store.close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
