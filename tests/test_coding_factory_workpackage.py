from __future__ import annotations

from pathlib import Path

import pytest

from orion_v3.coding_factory import (
    ArtifactStore,
    DecisionVerdict,
    FileOperation,
    ReviewVerdict,
    WorkPackageError,
    WorkPackageFactory,
    CodingFactoryBlackboard,
)
from orion_v3.state import EventType, LocalEventExchange, OrionStateStore, StateStoreError


def setup_factory(tmp_path: Path):
    db = tmp_path / "orion-core.db"
    store = OrionStateStore(db)
    store.initialize()
    project = store.create_project("ORION", project_id="orion")
    task = store.create_task(project.project_id, "Build WorkPackage V0", task_id="task-wp")
    exchange = LocalEventExchange(store)
    artifacts = ArtifactStore(tmp_path / "artifacts")
    factory = WorkPackageFactory(artifacts)
    board = CodingFactoryBlackboard(store, exchange)
    return store, exchange, artifacts, factory, board, project, task


def make_package(factory: WorkPackageFactory):
    file_artifact = factory.file_artifact(
        "src/orion_v3/example.py",
        "VALUE = 1\n",
        operation=FileOperation.REPLACE,
    )
    patch_artifact = factory.patch_artifact(
        "diff --git a/src/orion_v3/example.py b/src/orion_v3/example.py\n"
        "--- a/src/orion_v3/example.py\n"
        "+++ b/src/orion_v3/example.py\n"
        "@@\n"
        "-VALUE = 0\n"
        "+VALUE = 1\n"
    )
    return factory.create(
        project_id="orion",
        task_id="task-wp",
        attempt_id="attempt-001",
        base_sha="1" * 40,
        coder_provider="groq",
        coder_model="gpt-oss-120b",
        prompt_text="Make VALUE equal 1.",
        response_text="Structured candidate response.",
        artifacts=[file_artifact, patch_artifact],
        allowed_paths=["src/orion_v3"],
        forbidden_paths=["src/orion_v3/secrets"],
        verifier_spec={"checks": ["unit-tests"]},
    )


def test_artifact_store_deduplicates_and_detects_direct_tamper(tmp_path: Path):
    store = ArtifactStore(tmp_path / "artifacts")
    first = store.put_text("hello")
    second = store.put_text("hello")
    assert first.artifact_id == second.artifact_id
    assert store.read_text(first.artifact_id) == "hello"

    store.storage_path(first.artifact_id).write_bytes(b"tampered")
    with pytest.raises(Exception, match="integrity"):
        store.read_bytes(first.artifact_id)


def test_workpackage_hash_is_deterministic_and_manifest_reloads(tmp_path: Path):
    _, _, _, factory, _, _, _ = setup_factory(tmp_path)
    one = make_package(factory)
    two = make_package(factory)

    assert one.package_sha256 == two.package_sha256
    assert one.package_id == two.package_id
    assert one.manifest_artifact_id == two.manifest_artifact_id

    loaded = factory.load(one.manifest_artifact_id)
    assert loaded == one


def test_workpackage_rejects_bad_base_sha_and_out_of_scope_file(tmp_path: Path):
    _, _, _, factory, _, _, _ = setup_factory(tmp_path)
    artifact = factory.file_artifact(
        "docs/outside.txt",
        "x",
        operation=FileOperation.CREATE,
    )
    with pytest.raises(WorkPackageError, match="outside allowed"):
        factory.create(
            project_id="orion",
            task_id="task-wp",
            attempt_id="attempt-1",
            base_sha="1" * 40,
            coder_provider="groq",
            coder_model="model",
            prompt_text="x",
            response_text="y",
            artifacts=[artifact],
            allowed_paths=["src/orion_v3"],
            forbidden_paths=[],
            verifier_spec={},
        )

    good = factory.file_artifact(
        "src/orion_v3/x.py",
        "x=1\n",
        operation=FileOperation.CREATE,
    )
    with pytest.raises(WorkPackageError, match="base_sha"):
        factory.create(
            project_id="orion",
            task_id="task-wp",
            attempt_id="attempt-1",
            base_sha="not-a-sha",
            coder_provider="groq",
            coder_model="model",
            prompt_text="x",
            response_text="y",
            artifacts=[good],
            allowed_paths=["src/orion_v3"],
            forbidden_paths=[],
            verifier_spec={},
        )


def test_blackboard_binds_review_and_decision_to_exact_package(tmp_path: Path):
    store, _, _, factory, board, _, _ = setup_factory(tmp_path)
    package = make_package(factory)

    proposal = board.submit_candidate(package)
    review = board.review_candidate(
        package,
        proposal.event_id,
        reviewer_provider="groq",
        reviewer_model="qwen3.8-27b",
        verdict=ReviewVerdict.ACCEPTABLE,
        findings=["Package is within scope."],
    )
    decision = board.decide_candidate(
        package,
        review.event_id,
        verdict=DecisionVerdict.ACCEPT_CANDIDATE,
        decided_by="policy",
    )

    events = store.list_task_events("orion", "task-wp", limit=10)
    assert [item.event_type for item in events] == [
        EventType.PROPOSAL,
        EventType.REVIEW,
        EventType.DECISION,
    ]
    assert events[1].parent_event_id == proposal.event_id
    assert events[2].parent_event_id == review.event_id
    assert events[0].payload["body"]["package_sha256"] == package.package_sha256
    assert events[1].payload["body"]["package_sha256"] == package.package_sha256
    assert events[2].payload["body"]["package_sha256"] == package.package_sha256
    assert events[2].payload["body"]["execution_authority"] is False
    assert not any(item.event_type == EventType.ACTION for item in events)


def test_review_cannot_be_reused_for_different_package(tmp_path: Path):
    _, _, _, factory, board, _, _ = setup_factory(tmp_path)
    package1 = make_package(factory)
    proposal = board.submit_candidate(package1)
    review = board.review_candidate(
        package1,
        proposal.event_id,
        reviewer_provider="groq",
        reviewer_model="qwen3.8-27b",
        verdict=ReviewVerdict.ACCEPTABLE,
    )

    extra = factory.file_artifact(
        "src/orion_v3/other.py",
        "OTHER = 2\n",
        operation=FileOperation.CREATE,
    )
    package2 = factory.create(
        project_id="orion",
        task_id="task-wp",
        attempt_id="attempt-002",
        base_sha="1" * 40,
        coder_provider="groq",
        coder_model="gpt-oss-120b",
        prompt_text="Add other.",
        response_text="Candidate 2.",
        artifacts=[extra],
        allowed_paths=["src/orion_v3"],
        forbidden_paths=[],
        verifier_spec={"checks": ["unit-tests"]},
    )

    with pytest.raises(StateStoreError, match="another WorkPackage"):
        board.decide_candidate(
            package2,
            review.event_id,
            verdict=DecisionVerdict.ACCEPT_CANDIDATE,
            decided_by="policy",
        )


def test_blackboard_persists_across_reopen(tmp_path: Path):
    store, _, artifacts, factory, board, _, _ = setup_factory(tmp_path)
    package = make_package(factory)
    proposal = board.submit_candidate(package)
    review = board.review_candidate(
        package,
        proposal.event_id,
        reviewer_provider="groq",
        reviewer_model="qwen3.8-27b",
        verdict=ReviewVerdict.REPAIR_REQUIRED,
        findings=["Need one change."],
    )
    store.close()

    reopened = OrionStateStore(tmp_path / "orion-core.db")
    reopened.initialize()
    reloaded_factory = WorkPackageFactory(ArtifactStore(tmp_path / "artifacts"))
    loaded = reloaded_factory.load(package.manifest_artifact_id)
    assert loaded.package_sha256 == package.package_sha256
    assert reopened.get_event(proposal.event_id) is not None
    assert reopened.get_event(review.event_id) is not None
