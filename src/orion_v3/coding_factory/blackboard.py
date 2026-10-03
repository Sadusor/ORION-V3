from __future__ import annotations

from enum import Enum
from typing import Iterable

from orion_v3.state import (
    AttemptLease,
    EventRecord,
    EventType,
    LocalEventExchange,
    OrionStateStore,
    StateStoreError,
)

from .workpackage import WorkPackage, WorkPackageError


class ReviewVerdict(str, Enum):
    ACCEPTABLE = "ACCEPTABLE"
    REPAIR_REQUIRED = "REPAIR_REQUIRED"


class DecisionVerdict(str, Enum):
    ACCEPT_CANDIDATE = "ACCEPT_CANDIDATE"
    REJECT_CANDIDATE = "REJECT_CANDIDATE"


class CodingFactoryBlackboard:
    """Structured Coding Factory records over the immutable local exchange."""

    def __init__(
        self,
        store: OrionStateStore,
        exchange: LocalEventExchange,
    ) -> None:
        self.store = store
        self.exchange = exchange

    def submit_candidate(
        self,
        package: WorkPackage,
        *,
        recipient: str = "cloud_ai:reviewer",
    ) -> EventRecord:
        self._require_package_task(package)
        return self.exchange.publish(
            package.project_id,
            package.task_id,
            EventType.PROPOSAL,
            actor_kind="cloud_ai",
            actor_id=f"{package.coder_provider}:{package.coder_model}",
            recipient=recipient,
            body={
                "kind": "WORKPACKAGE_CANDIDATE",
                "package_id": package.package_id,
                "package_sha256": package.package_sha256,
                "manifest_artifact_id": package.manifest_artifact_id,
                "base_sha": package.base_sha,
                "coder_provider": package.coder_provider,
                "coder_model": package.coder_model,
            },
            attempt_id=package.attempt_id,
        ).event

    def review_candidate(
        self,
        package: WorkPackage,
        proposal_event_id: str,
        *,
        reviewer_provider: str,
        reviewer_model: str,
        verdict: ReviewVerdict,
        findings: Iterable[str] = (),
    ) -> EventRecord:
        self._require_package_task(package)
        proposal = self._require_package_event(
            package,
            proposal_event_id,
            expected_type=EventType.PROPOSAL,
        )
        clean_findings = tuple(
            item.strip()
            for item in findings
            if isinstance(item, str) and item.strip()
        )
        return self.exchange.publish(
            package.project_id,
            package.task_id,
            EventType.REVIEW,
            actor_kind="cloud_ai",
            actor_id=f"{reviewer_provider.strip()}:{reviewer_model.strip()}",
            recipient="orion",
            body={
                "kind": "WORKPACKAGE_REVIEW",
                "package_id": package.package_id,
                "package_sha256": package.package_sha256,
                "verdict": verdict.value,
                "findings": list(clean_findings),
            },
            parent_event_id=proposal.event_id,
            attempt_id=package.attempt_id,
        ).event

    def decide_candidate(
        self,
        package: WorkPackage,
        review_event_id: str,
        *,
        verdict: DecisionVerdict,
        decided_by: str,
    ) -> EventRecord:
        self._require_package_task(package)
        review = self._require_package_event(
            package,
            review_event_id,
            expected_type=EventType.REVIEW,
        )
        actor = decided_by.strip()
        if not actor:
            raise WorkPackageError("decided_by must be non-empty")
        return self.exchange.publish(
            package.project_id,
            package.task_id,
            EventType.DECISION,
            actor_kind="orion",
            actor_id=actor,
            recipient="coding_factory",
            body={
                "kind": "WORKPACKAGE_DECISION",
                "package_id": package.package_id,
                "package_sha256": package.package_sha256,
                "verdict": verdict.value,
                "execution_authority": False,
            },
            parent_event_id=review.event_id,
            attempt_id=package.attempt_id,
        ).event

    def authorize_execution(
        self,
        package: WorkPackage,
        decision_event_id: str,
        *,
        lease: AttemptLease,
        authorized_by: str,
    ) -> EventRecord:
        """Bind one accepted WorkPackage to the current Attempt lease generation."""
        self._require_package_task(package)
        decision = self._require_package_event(
            package,
            decision_event_id,
            expected_type=EventType.DECISION,
        )
        body = decision.payload.get("body")
        if not isinstance(body, dict):
            raise StateStoreError("WorkPackage decision has no body")
        if body.get("verdict") != DecisionVerdict.ACCEPT_CANDIDATE.value:
            raise StateStoreError("rejected WorkPackage cannot be authorized")
        if body.get("execution_authority") is not False:
            raise StateStoreError("unexpected WorkPackage decision authority state")

        actor = authorized_by.strip()
        if not actor:
            raise WorkPackageError("authorized_by must be non-empty")
        if (
            lease.attempt_id != package.attempt_id
            or lease.project_id != package.project_id
            or lease.task_id != package.task_id
        ):
            raise StateStoreError("Attempt lease does not belong to WorkPackage")

        return self.exchange.publish(
            package.project_id,
            package.task_id,
            EventType.ACTION,
            actor_kind="orion",
            actor_id=actor,
            recipient="coding_factory_executor",
            body={
                "kind": "WORKPACKAGE_EXECUTION_AUTHORIZATION",
                "package_id": package.package_id,
                "package_sha256": package.package_sha256,
                "manifest_artifact_id": package.manifest_artifact_id,
                "base_sha": package.base_sha,
                "attempt_id": package.attempt_id,
                "lease_generation": lease.generation,
                "worker_id": lease.worker_id,
                "execution_authority": True,
            },
            parent_event_id=decision.event_id,
            attempt_id=package.attempt_id,
        ).event

    def _require_package_task(self, package: WorkPackage) -> None:
        task = self.store.get_task(package.task_id)
        if task is None:
            raise StateStoreError("WorkPackage task does not exist")
        if task.project_id != package.project_id:
            raise StateStoreError("WorkPackage task belongs to another project")

    def _require_package_event(
        self,
        package: WorkPackage,
        event_id: str,
        *,
        expected_type: EventType,
    ) -> EventRecord:
        event = self.store.get_event(event_id)
        if event is None:
            raise StateStoreError("referenced Coding Factory event does not exist")
        if event.project_id != package.project_id or event.task_id != package.task_id:
            raise StateStoreError("referenced Coding Factory event is out of scope")
        if event.event_type != expected_type:
            raise StateStoreError("referenced Coding Factory event has wrong type")
        body = event.payload.get("body")
        if not isinstance(body, dict):
            raise StateStoreError("referenced Coding Factory event has no body")
        if body.get("package_id") != package.package_id:
            raise StateStoreError("referenced event belongs to another WorkPackage")
        if body.get("package_sha256") != package.package_sha256:
            raise StateStoreError("referenced event package hash mismatch")
        return event
