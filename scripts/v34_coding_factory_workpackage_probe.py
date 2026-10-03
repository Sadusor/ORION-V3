from __future__ import annotations

import tempfile
from pathlib import Path

from orion_v3.coding_factory import (
    ArtifactStore,
    CodingFactoryBlackboard,
    DecisionVerdict,
    FileOperation,
    ReviewVerdict,
    WorkPackageError,
    WorkPackageFactory,
)
from orion_v3.state import EventType, LocalEventExchange, OrionStateStore, StateStoreError


def main() -> int:
    print("V3_RUN_ID> V3-RUN-018")
    print("CODING_FACTORY_WORKPACKAGE_GATE> START")

    with tempfile.TemporaryDirectory(prefix="orion-v3-workpackage-") as temp:
        root = Path(temp)
        db_path = root / "orion-core.db"
        artifact_root = root / "artifacts"

        store = OrionStateStore(db_path)
        store.initialize()
        project = store.create_project("ORION", project_id="orion")
        task = store.create_task(
            project.project_id,
            "Prove immutable Coding Factory candidate package",
            task_id="task-wp",
        )
        exchange = LocalEventExchange(store)
        artifacts = ArtifactStore(artifact_root)
        factory = WorkPackageFactory(artifacts)
        board = CodingFactoryBlackboard(store, exchange)

        same1 = artifacts.put_text("same-bytes")
        same2 = artifacts.put_text("same-bytes")
        assert same1.artifact_id == same2.artifact_id
        assert artifacts.read_text(same1.artifact_id) == "same-bytes"
        print("ARTIFACT_DEDUPLICATION> PASS")

        tamper = artifacts.put_text("integrity")
        artifacts.storage_path(tamper.artifact_id).write_bytes(b"tampered")
        try:
            artifacts.read_bytes(tamper.artifact_id)
        except Exception:
            pass
        else:
            raise AssertionError("tampered artifact unexpectedly read")
        print("ARTIFACT_TAMPER_DETECTION> PASS")

        file_ref = factory.file_artifact(
            "src/orion_v3/example.py",
            "VALUE = 1\n",
            operation=FileOperation.REPLACE,
        )
        patch_ref = factory.patch_artifact(
            "diff --git a/src/orion_v3/example.py b/src/orion_v3/example.py\n"
            "--- a/src/orion_v3/example.py\n"
            "+++ b/src/orion_v3/example.py\n"
            "@@\n"
            "-VALUE = 0\n"
            "+VALUE = 1\n",
            target_paths=["src/orion_v3/example.py"],
        )

        package = factory.create(
            project_id=project.project_id,
            task_id=task.task_id,
            attempt_id="attempt-001",
            base_sha="1" * 40,
            coder_provider="groq",
            coder_model="gpt-oss-120b",
            prompt_text="Set VALUE to 1.",
            response_text="Structured WorkPackage candidate.",
            artifacts=[file_ref, patch_ref],
            allowed_paths=["src/orion_v3"],
            forbidden_paths=["src/orion_v3/secrets"],
            verifier_spec={"checks": ["unit-tests"]},
        )
        package_again = factory.create(
            project_id=project.project_id,
            task_id=task.task_id,
            attempt_id="attempt-001",
            base_sha="1" * 40,
            coder_provider="groq",
            coder_model="gpt-oss-120b",
            prompt_text="Set VALUE to 1.",
            response_text="Structured WorkPackage candidate.",
            artifacts=[file_ref, patch_ref],
            allowed_paths=["src/orion_v3"],
            forbidden_paths=["src/orion_v3/secrets"],
            verifier_spec={"checks": ["unit-tests"]},
        )
        assert package.package_sha256 == package_again.package_sha256
        assert package.manifest_artifact_id == package_again.manifest_artifact_id
        loaded = factory.load(package.manifest_artifact_id)
        assert loaded == package
        print("DETERMINISTIC_PACKAGE_IDENTITY> PASS")
        print("PACKAGE_MANIFEST_RELOAD> PASS")

        bad_file = factory.file_artifact(
            "docs/outside.txt",
            "outside\n",
            operation=FileOperation.CREATE,
        )
        try:
            factory.create(
                project_id=project.project_id,
                task_id=task.task_id,
                attempt_id="attempt-bad-file",
                base_sha="1" * 40,
                coder_provider="groq",
                coder_model="coder",
                prompt_text="x",
                response_text="y",
                artifacts=[bad_file],
                allowed_paths=["src/orion_v3"],
                forbidden_paths=[],
                verifier_spec={},
            )
        except WorkPackageError:
            pass
        else:
            raise AssertionError("out-of-scope FILE unexpectedly accepted")
        print("OUT_OF_SCOPE_FILE> DENIED")

        bad_patch = factory.patch_artifact(
            "diff --git a/docs/outside.txt b/docs/outside.txt\n"
            "--- a/docs/outside.txt\n"
            "+++ b/docs/outside.txt\n"
            "@@\n-old\n+new\n",
            target_paths=["docs/outside.txt"],
        )
        try:
            factory.create(
                project_id=project.project_id,
                task_id=task.task_id,
                attempt_id="attempt-bad-patch",
                base_sha="1" * 40,
                coder_provider="groq",
                coder_model="coder",
                prompt_text="x",
                response_text="y",
                artifacts=[bad_patch],
                allowed_paths=["src/orion_v3"],
                forbidden_paths=[],
                verifier_spec={},
            )
        except WorkPackageError:
            pass
        else:
            raise AssertionError("out-of-scope PATCH target unexpectedly accepted")
        print("OUT_OF_SCOPE_PATCH_TARGET> DENIED")

        try:
            factory.create(
                project_id=project.project_id,
                task_id=task.task_id,
                attempt_id="attempt-bad-sha",
                base_sha="HEAD",
                coder_provider="groq",
                coder_model="coder",
                prompt_text="x",
                response_text="y",
                artifacts=[file_ref],
                allowed_paths=["src/orion_v3"],
                forbidden_paths=[],
                verifier_spec={},
            )
        except WorkPackageError:
            pass
        else:
            raise AssertionError("non-exact base SHA unexpectedly accepted")
        print("NON_EXACT_BASE_SHA> DENIED")

        proposal = board.submit_candidate(package)
        review = board.review_candidate(
            package,
            proposal.event_id,
            reviewer_provider="groq",
            reviewer_model="qwen3.8-27b",
            verdict=ReviewVerdict.ACCEPTABLE,
            findings=["Scope and package identity are coherent."],
        )
        decision = board.decide_candidate(
            package,
            review.event_id,
            verdict=DecisionVerdict.ACCEPT_CANDIDATE,
            decided_by="policy",
        )

        chain = store.list_task_events(project.project_id, task.task_id, limit=10)
        assert [event.event_type for event in chain] == [
            EventType.PROPOSAL,
            EventType.REVIEW,
            EventType.DECISION,
        ]
        assert chain[1].parent_event_id == proposal.event_id
        assert chain[2].parent_event_id == review.event_id
        assert all(
            event.payload["body"]["package_sha256"] == package.package_sha256
            for event in chain
        )
        assert decision.payload["body"]["execution_authority"] is False
        assert not any(event.event_type == EventType.ACTION for event in chain)
        print("PACKAGE_BOUND_REVIEW_DECISION_CHAIN> PASS")
        print("CANDIDATE_EXECUTION_AUTHORITY> NONE")

        other_file = factory.file_artifact(
            "src/orion_v3/other.py",
            "OTHER = 2\n",
            operation=FileOperation.CREATE,
        )
        other_package = factory.create(
            project_id=project.project_id,
            task_id=task.task_id,
            attempt_id="attempt-002",
            base_sha="1" * 40,
            coder_provider="groq",
            coder_model="gpt-oss-120b",
            prompt_text="Add other.",
            response_text="Other package.",
            artifacts=[other_file],
            allowed_paths=["src/orion_v3"],
            forbidden_paths=[],
            verifier_spec={"checks": ["unit-tests"]},
        )
        try:
            board.decide_candidate(
                other_package,
                review.event_id,
                verdict=DecisionVerdict.ACCEPT_CANDIDATE,
                decided_by="policy",
            )
        except StateStoreError:
            pass
        else:
            raise AssertionError("review from another package was reused")
        print("CROSS_PACKAGE_REVIEW_REUSE> DENIED")

        store.close()
        reopened = OrionStateStore(db_path)
        reopened.initialize()
        reopened_factory = WorkPackageFactory(ArtifactStore(artifact_root))
        reloaded = reopened_factory.load(package.manifest_artifact_id)
        assert reloaded.package_sha256 == package.package_sha256
        assert reopened.get_event(proposal.event_id) is not None
        assert reopened.get_event(review.event_id) is not None
        assert reopened.get_event(decision.event_id) is not None
        print("PACKAGE_BLACKBOARD_REOPEN_PERSISTENCE> PASS")

        print("NETWORK_MODEL_EXECUTION_DEPENDENCY> NONE")
        print("CODING_FACTORY_WORKPACKAGE_GATE> PASS")
        print("STATUS> PASS")
        reopened.close()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
