from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

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
from orion_v3.state import AttemptAuthority, AttemptDenied, LocalEventExchange, OrionStateStore


class Clock:
    def __init__(self, value: float = 1000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


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


def init_repo(root: Path) -> tuple[Path, str]:
    repo = root / "source"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.name", "ORION Test")
    git(repo, "config", "user.email", "orion-test@example.invalid")
    (repo / "src").mkdir()
    (repo / "src" / "value.txt").write_text("VALUE=0\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "outside.txt").write_text("outside\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "base")
    return repo, git(repo, "rev-parse", "HEAD")


def build_file_case(tmp_path: Path, *, verifier_sha: str | None = None):
    source_repo, base_sha = init_repo(tmp_path)
    store = OrionStateStore(tmp_path / "core.db")
    store.initialize()
    project = store.create_project("ORION", project_id="orion")
    task = store.create_task(project.project_id, "bounded execution", task_id="task-exec")

    clock = Clock()
    raw_tokens = iter(["raw-a", "raw-b", "raw-c"])
    attempts = AttemptAuthority(
        store,
        clock=clock,
        token_factory=lambda: next(raw_tokens),
    )
    attempts.initialize()
    attempt = attempts.create_attempt(task.task_id, attempt_id="attempt-exec")

    artifacts = ArtifactStore(tmp_path / "artifacts")
    factory = WorkPackageFactory(artifacts)
    payload = "bounded workpackage execution\n"
    artifact = factory.file_artifact(
        "scratch/probe.txt",
        payload,
        operation=FileOperation.CREATE,
    )
    expected = verifier_sha or hashlib.sha256(payload.encode("utf-8")).hexdigest()
    package = factory.create(
        project_id=project.project_id,
        task_id=task.task_id,
        attempt_id=attempt.attempt_id,
        base_sha=base_sha,
        coder_provider="fixture",
        coder_model="deterministic",
        prompt_text="create harmless probe",
        response_text="structured candidate",
        artifacts=[artifact],
        allowed_paths=["scratch"],
        forbidden_paths=["scratch/forbidden"],
        verifier_spec={
            "kind": "file_sha256",
            "path": "scratch/probe.txt",
            "sha256": expected,
        },
    )

    exchange = LocalEventExchange(store)
    board = CodingFactoryBlackboard(store, exchange)
    proposal = board.submit_candidate(package)
    review = board.review_candidate(
        package,
        proposal.event_id,
        reviewer_provider="fixture",
        reviewer_model="reviewer",
        verdict=ReviewVerdict.ACCEPTABLE,
        findings=["bounded"],
    )
    decision = board.decide_candidate(
        package,
        review.event_id,
        verdict=DecisionVerdict.ACCEPT_CANDIDATE,
        decided_by="policy",
    )
    issued = attempts.claim(
        attempt.attempt_id,
        worker_id="worker-a",
        ttl_seconds=30,
    )
    action = board.authorize_execution(
        package,
        decision.event_id,
        lease=issued.lease,
        authorized_by="policy",
    )
    executor = WorkPackageExecutor(
        store=store,
        attempts=attempts,
        factory=factory,
        source_repo=source_repo,
        worktree_root=tmp_path / "worktrees",
    )
    return {
        "store": store,
        "clock": clock,
        "attempts": attempts,
        "attempt": attempt,
        "factory": factory,
        "package": package,
        "board": board,
        "issued": issued,
        "action": action,
        "executor": executor,
        "source_repo": source_repo,
        "base_sha": base_sha,
        "worktree_root": tmp_path / "worktrees",
    }


def test_exact_sha_file_package_executes_and_cleans_worktree(tmp_path):
    case = build_file_case(tmp_path)

    evidence = case["executor"].run(
        manifest_artifact_id=case["package"].manifest_artifact_id,
        expected_package_sha256=case["package"].package_sha256,
        action_event_id=case["action"].event_id,
        lease_token=case["issued"].token,
    )

    assert evidence.base_sha == case["base_sha"]
    assert evidence.changed_paths == ("scratch/probe.txt",)
    assert len(evidence.diff_sha256) == 64
    assert len(evidence.result_tree_sha) == 40
    assert evidence.verifier["status"] == "PASS"
    assert case["attempts"].get_attempt(case["attempt"].attempt_id).status == "SUCCEEDED"
    assert git(case["source_repo"], "rev-parse", "HEAD") == case["base_sha"]
    assert git(case["source_repo"], "status", "--porcelain=v1") == ""
    assert not any(case["worktree_root"].iterdir())
    assert "push" not in evidence.git_subcommands
    assert "merge" not in evidence.git_subcommands
    assert "commit" not in evidence.git_subcommands

    events = case["store"].list_task_events("orion", "task-exec", limit=20)
    assert [event.event_type.value for event in events] == [
        "PROPOSAL",
        "REVIEW",
        "DECISION",
        "ACTION",
        "EVIDENCE",
        "RESULT",
    ]


def test_stop_after_prepare_denies_effect_and_cleans_worktree(tmp_path):
    case = build_file_case(tmp_path)
    prepared = case["executor"].prepare(
        manifest_artifact_id=case["package"].manifest_artifact_id,
        expected_package_sha256=case["package"].package_sha256,
        action_event_id=case["action"].event_id,
        lease_token=case["issued"].token,
    )
    assert prepared.worktree.exists()

    case["attempts"].stop(
        case["attempt"].attempt_id,
        requested_by="owner",
        reason="stop probe",
    )

    with pytest.raises(AttemptDenied) as exc:
        case["executor"].continue_execution(
            prepared,
            lease_token=case["issued"].token,
        )
    assert exc.value.code == "stopped_attempt"
    assert not prepared.worktree.exists()
    assert case["attempts"].get_attempt(case["attempt"].attempt_id).status == "STOPPED"


def test_verifier_failure_marks_attempt_failed_and_cleans(tmp_path):
    case = build_file_case(tmp_path, verifier_sha="0" * 64)

    with pytest.raises(ExecutionDenied) as exc:
        case["executor"].run(
            manifest_artifact_id=case["package"].manifest_artifact_id,
            expected_package_sha256=case["package"].package_sha256,
            action_event_id=case["action"].event_id,
            lease_token=case["issued"].token,
        )
    assert exc.value.code == "verifier_failed"
    assert case["attempts"].get_attempt(case["attempt"].attempt_id).status == "FAILED"
    assert not any(case["worktree_root"].iterdir())
    assert git(case["source_repo"], "status", "--porcelain=v1") == ""


def test_actual_patch_paths_are_verified_not_claimed_targets(tmp_path):
    source_repo, base_sha = init_repo(tmp_path)
    store = OrionStateStore(tmp_path / "core.db")
    store.initialize()
    project = store.create_project("ORION", project_id="orion")
    task = store.create_task(project.project_id, "dishonest patch probe", task_id="task-patch")
    attempts = AttemptAuthority(store, token_factory=lambda: "raw-patch")
    attempts.initialize()
    attempt = attempts.create_attempt(task.task_id, attempt_id="attempt-patch")

    artifacts = ArtifactStore(tmp_path / "artifacts")
    factory = WorkPackageFactory(artifacts)
    patch = factory.patch_artifact(
        "diff --git a/docs/outside.txt b/docs/outside.txt\n"
        "--- a/docs/outside.txt\n"
        "+++ b/docs/outside.txt\n"
        "@@ -1 +1 @@\n"
        "-outside\n"
        "+tampered\n",
        target_paths=["src/value.txt"],
    )
    package = factory.create(
        project_id=project.project_id,
        task_id=task.task_id,
        attempt_id=attempt.attempt_id,
        base_sha=base_sha,
        coder_provider="fixture",
        coder_model="dishonest",
        prompt_text="change value",
        response_text="claims safe target",
        artifacts=[patch],
        allowed_paths=["src"],
        forbidden_paths=[],
        verifier_spec={
            "kind": "file_sha256",
            "path": "src/value.txt",
            "sha256": hashlib.sha256(b"VALUE=0\n").hexdigest(),
        },
    )
    board = CodingFactoryBlackboard(store, LocalEventExchange(store))
    proposal = board.submit_candidate(package)
    review = board.review_candidate(
        package,
        proposal.event_id,
        reviewer_provider="fixture",
        reviewer_model="reviewer",
        verdict=ReviewVerdict.ACCEPTABLE,
    )
    decision = board.decide_candidate(
        package,
        review.event_id,
        verdict=DecisionVerdict.ACCEPT_CANDIDATE,
        decided_by="policy",
    )
    issued = attempts.claim(attempt.attempt_id, worker_id="worker", ttl_seconds=30)
    action = board.authorize_execution(
        package,
        decision.event_id,
        lease=issued.lease,
        authorized_by="policy",
    )
    executor = WorkPackageExecutor(
        store=store,
        attempts=attempts,
        factory=factory,
        source_repo=source_repo,
        worktree_root=tmp_path / "worktrees",
    )

    with pytest.raises(ExecutionDenied) as exc:
        executor.run(
            manifest_artifact_id=package.manifest_artifact_id,
            expected_package_sha256=package.package_sha256,
            action_event_id=action.event_id,
            lease_token=issued.token,
        )
    assert exc.value.code == "changed_path_out_of_scope"
    assert attempts.get_attempt(attempt.attempt_id).status == "FAILED"
    assert not any((tmp_path / "worktrees").iterdir())
    assert (source_repo / "docs" / "outside.txt").read_text(encoding="utf-8") == "outside\n"


def test_old_action_is_stale_after_lease_generation_changes(tmp_path):
    case = build_file_case(tmp_path)
    first = case["issued"]
    case["clock"].value = first.lease.expires_at
    second = case["attempts"].claim(
        case["attempt"].attempt_id,
        worker_id="worker-b",
        ttl_seconds=30,
    )

    with pytest.raises(ExecutionDenied) as exc:
        case["executor"].prepare(
            manifest_artifact_id=case["package"].manifest_artifact_id,
            expected_package_sha256=case["package"].package_sha256,
            action_event_id=case["action"].event_id,
            lease_token=second.token,
        )
    assert exc.value.code == "stale_execution_authorization"
    assert not any(case["worktree_root"].iterdir())


def test_wrong_package_hash_is_denied_before_worktree(tmp_path):
    case = build_file_case(tmp_path)
    with pytest.raises(ExecutionDenied) as exc:
        case["executor"].prepare(
            manifest_artifact_id=case["package"].manifest_artifact_id,
            expected_package_sha256="0" * 64,
            action_event_id=case["action"].event_id,
            lease_token=case["issued"].token,
        )
    assert exc.value.code == "package_hash_mismatch"
    assert not any(case["worktree_root"].iterdir())


def test_changed_python_must_pass_authoring_preflight(tmp_path):
    source_repo, base_sha = init_repo(tmp_path)
    store = OrionStateStore(tmp_path / "core.db")
    store.initialize()
    project = store.create_project("ORION", project_id="orion")
    task = store.create_task(project.project_id, "syntax guard probe", task_id="task-syntax")
    attempts = AttemptAuthority(store, token_factory=lambda: "raw-syntax")
    attempts.initialize()
    attempt = attempts.create_attempt(task.task_id, attempt_id="attempt-syntax")

    artifacts = ArtifactStore(tmp_path / "artifacts")
    factory = WorkPackageFactory(artifacts)
    broken_source = "from math import (\\n    sqrt,\\n)\\n"
    artifact = factory.file_artifact(
        "scratch/broken.py",
        broken_source,
        operation=FileOperation.CREATE,
    )
    package = factory.create(
        project_id=project.project_id,
        task_id=task.task_id,
        attempt_id=attempt.attempt_id,
        base_sha=base_sha,
        coder_provider="fixture",
        coder_model="syntax-bug",
        prompt_text="create source",
        response_text="malformed source",
        artifacts=[artifact],
        allowed_paths=["scratch"],
        forbidden_paths=[],
        verifier_spec={
            "kind": "file_sha256",
            "path": "scratch/broken.py",
            "sha256": hashlib.sha256(broken_source.encode("utf-8")).hexdigest(),
        },
    )
    board = CodingFactoryBlackboard(store, LocalEventExchange(store))
    proposal = board.submit_candidate(package)
    review = board.review_candidate(
        package,
        proposal.event_id,
        reviewer_provider="fixture",
        reviewer_model="reviewer",
        verdict=ReviewVerdict.ACCEPTABLE,
    )
    decision = board.decide_candidate(
        package,
        review.event_id,
        verdict=DecisionVerdict.ACCEPT_CANDIDATE,
        decided_by="policy",
    )
    issued = attempts.claim(attempt.attempt_id, worker_id="worker", ttl_seconds=30)
    action = board.authorize_execution(
        package,
        decision.event_id,
        lease=issued.lease,
        authorized_by="policy",
    )
    executor = WorkPackageExecutor(
        store=store,
        attempts=attempts,
        factory=factory,
        source_repo=source_repo,
        worktree_root=tmp_path / "worktrees",
    )

    with pytest.raises(ExecutionDenied) as exc:
        executor.run(
            manifest_artifact_id=package.manifest_artifact_id,
            expected_package_sha256=package.package_sha256,
            action_event_id=action.event_id,
            lease_token=issued.token,
        )
    assert exc.value.code == "authoring_preflight_failed"
    assert attempts.get_attempt(attempt.attempt_id).status == "FAILED"
    assert not any((tmp_path / "worktrees").iterdir())
