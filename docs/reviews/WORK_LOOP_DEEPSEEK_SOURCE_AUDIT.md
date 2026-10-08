# ORION V3 Work Loop — DeepSeek Code Audit Bundle

Source: Sadusor/ORION-V3. This is a source snapshot for independent audit, not proof of runtime safety.

Review priorities: authorization nonce replay, STOP race, evidence authenticity, policy bypass, symlink/TOCTOU, Windows ACL isolation, vault atomicity, crash recovery. Separate confirmed defects from risks. Real execution is disabled.

## src/orion_v3/work_loop/coordinator.py

```python
"""Safe, deterministic coordinator for the existing Work Loop modules.

This module deliberately does not launch a subprocess or modify source files.
A real Work Hand must remain disabled until isolation is independently proven.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .authorization import issue_authorization
from .contracts import EvidenceRecord, Proposal, RiskClass
from .simulated_hand import SimulatedWorkHand
from .engine import WorkLoopEngine
from .executor import ExecutionRequest
from .stop import StopSource


@dataclass(frozen=True, slots=True)
class CycleOutcome:
    status: str
    reason: str
    evidence: EvidenceRecord | None = None


class WorkLoopCoordinator:
    """Connect the existing policy, authorization, executor and verifier seams."""

    def __init__(self, engine: WorkLoopEngine, *, secret: bytes, source_revision: str, stop: StopSource):
        self.engine = engine
        self.secret = secret
        self.source_revision = source_revision
        self.stop = stop
        self.executor = SimulatedWorkHand(secret=secret, source_revision=source_revision)

    def cycle(self, proposal: Proposal) -> CycleOutcome:
        if self.stop.stop_requested():
            return CycleOutcome("stopped", "authoritative STOP requested")
        prepared = self.engine.prepare(proposal)
        if prepared.policy.risk == RiskClass.RED:
            return CycleOutcome("denied", prepared.policy.reason)
        if prepared.policy.risk == RiskClass.YELLOW or not prepared.policy.allowed_to_execute:
            return CycleOutcome("awaiting_owner", prepared.policy.reason)
        if self.stop.stop_requested():
            return CycleOutcome("stopped", "authoritative STOP requested")
        expires = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
        auth = issue_authorization(proposal, RiskClass.GREEN, expires, self.secret)
        evidence = self.executor.execute(ExecutionRequest(proposal, auth))
        if self.stop.stop_requested():
            return CycleOutcome("stopped", "STOP requested before evidence commit", evidence)
        if evidence.verdict != "indeterminate":
            return CycleOutcome("blocked", "dry-run executor returned unexpected verdict", evidence)
        checked = self.engine.apply_evidence(
            proposal, evidence, required_type="execution",
            expected_source_revision=self.source_revision,
            next_action_on_pass="await next task",
            next_action_on_fail="await qualified executor",
        )
        if not checked.verification.accepted:
            return CycleOutcome("blocked", checked.verification.reason, evidence)
        return CycleOutcome("dry_run", "no operation executed; qualification still required", evidence)

```

## src/orion_v3/work_loop/simulated_hand.py

```python
"""Independent simulated Work Hand: never performs real I/O.

Strictly validates exact authorization and models a bounded operation.
The coordinator still treats all simulated evidence as indeterminate.
"""
from __future__ import annotations

from .authorization import verify_authorization
from .contracts import EvidenceRecord
from .executor import ExecutionRequest


class SimulatedWorkHand:
    def __init__(self, *, secret: bytes, source_revision: str):
        self._secret = secret
        self._revision = source_revision

    def execute(self, request: ExecutionRequest) -> EvidenceRecord:
        p = request.proposal
        authorized = verify_authorization(request.authorization, p, self._secret)
        return EvidenceRecord(
            p.project_id, p.task_id, p.proposal_hash, "execution",
            "indeterminate" if authorized else "fail",
            "orion-simulated-work-hand", self._revision,
            "SIMULATION ONLY: no source file, process, or network operation executed"
            if authorized else "authorization rejected; nothing executed",
        )

```

## src/orion_v3/work_loop/authorization.py

```python
"""Exact-proposal authorization tokens inspired by the audited OpenMuse pattern."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
import secrets

from .contracts import Proposal, RiskClass


@dataclass(frozen=True, slots=True)
class Authorization:
    project_id: str
    task_id: str
    proposal_hash: str
    risk: RiskClass
    expires_at: str
    nonce: str
    signature: str


def _payload(project_id: str, task_id: str, proposal_hash: str, risk: RiskClass, expires_at: str, nonce: str) -> bytes:
    return json.dumps(
        [project_id, task_id, proposal_hash, risk.value, expires_at, nonce],
        separators=(",", ":"),
    ).encode("utf-8")


def issue_authorization(proposal: Proposal, risk: RiskClass, expires_at: str, secret: bytes) -> Authorization:
    if risk == RiskClass.RED:
        raise ValueError("RED proposals cannot be authorized")
    nonce = secrets.token_hex(16)
    signature = hmac.new(
        secret,
        _payload(proposal.project_id, proposal.task_id, proposal.proposal_hash, risk, expires_at, nonce),
        hashlib.sha256,
    ).hexdigest()
    return Authorization(proposal.project_id, proposal.task_id, proposal.proposal_hash, risk, expires_at, nonce, signature)


def verify_authorization(auth: Authorization, proposal: Proposal, secret: bytes, now: datetime | None = None) -> bool:
    if auth.project_id != proposal.project_id or auth.task_id != proposal.task_id:
        return False
    if auth.proposal_hash != proposal.proposal_hash or auth.risk == RiskClass.RED:
        return False
    try:
        expiry = datetime.fromisoformat(auth.expires_at)
    except ValueError:
        return False
    if expiry.tzinfo is None:
        return False
    now = now or datetime.now(timezone.utc)
    if expiry <= now:
        return False
    expected = hmac.new(
        secret,
        _payload(auth.project_id, auth.task_id, auth.proposal_hash, auth.risk, auth.expires_at, auth.nonce),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(auth.signature, expected)

```

## src/orion_v3/work_loop/engine.py

```python
"""Pure state-machine seam for Autonomous Work Loop V1.

No model and no Hand are embedded here.  Callers supply a Proposal and later an
EvidenceRecord.  This keeps Qwen and TheHands replaceable and makes the authority
transition independently testable.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import EvidenceRecord, Proposal, RiskClass
from .policy import PolicyDecision, classify_proposal
from .vault import ProjectVault
from .verifier import VerificationResult, verify_evidence


@dataclass(frozen=True, slots=True)
class PreparedWork:
    proposal: Proposal
    policy: PolicyDecision


@dataclass(frozen=True, slots=True)
class AppliedEvidence:
    verification: VerificationResult
    state_updated: bool


class WorkLoopEngine:
    def __init__(self, vault: ProjectVault):
        self.vault = vault

    def prepare(self, proposal: Proposal) -> PreparedWork:
        state = self.vault.load()
        if proposal.project_id != state.project_id:
            return PreparedWork(
                proposal,
                PolicyDecision(RiskClass.RED, False, "proposal belongs to another project"),
            )
        if proposal.task_id != state.current_task:
            return PreparedWork(
                proposal,
                PolicyDecision(RiskClass.RED, False, "proposal is not for current task"),
            )
        return PreparedWork(proposal, classify_proposal(proposal, state.frozen_paths))

    def apply_evidence(
        self,
        proposal: Proposal,
        evidence: EvidenceRecord,
        *,
        required_type: str,
        expected_source_revision: str | None,
        next_action_on_pass: str,
        next_action_on_fail: str,
    ) -> AppliedEvidence:
        prepared = self.prepare(proposal)
        if prepared.policy.risk == RiskClass.RED:
            return AppliedEvidence(
                VerificationResult(False, "indeterminate", "proposal is RED"),
                False,
            )
        verification = verify_evidence(
            proposal,
            evidence,
            required_type=required_type,
            expected_source_revision=expected_source_revision,
        )
        if not verification.accepted:
            return AppliedEvidence(verification, False)
        next_action = (
            next_action_on_pass if verification.verdict == "pass" else next_action_on_fail
        )
        self.vault.record_verified_result(
            evidence,
            next_action=next_action,
            blocked=verification.verdict != "pass",
        )
        return AppliedEvidence(verification, True)

```

## src/orion_v3/work_loop/verifier.py

```python
"""Evidence authentication/type checks for the minimal loop."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import EvidenceRecord, Proposal


VALID_EVIDENCE_TYPES = frozenset({"git_check", "execution", "test", "benchmark", "lint", "manual"})
VALID_VERDICTS = frozenset({"pass", "fail", "malformed", "indeterminate"})


@dataclass(frozen=True, slots=True)
class VerificationResult:
    accepted: bool
    verdict: str
    reason: str


def verify_evidence(
    proposal: Proposal,
    evidence: EvidenceRecord,
    *,
    required_type: str | None = None,
    expected_source_revision: str | None = None,
) -> VerificationResult:
    if evidence.project_id != proposal.project_id or evidence.task_id != proposal.task_id:
        return VerificationResult(False, "indeterminate", "evidence belongs to another task")
    if evidence.proposal_hash != proposal.proposal_hash:
        return VerificationResult(False, "indeterminate", "evidence proposal hash mismatch")
    if evidence.evidence_type not in VALID_EVIDENCE_TYPES:
        return VerificationResult(False, "malformed", "unknown evidence type")
    if evidence.verdict not in VALID_VERDICTS:
        return VerificationResult(False, "malformed", "unknown evidence verdict")
    if required_type is not None and evidence.evidence_type != required_type:
        return VerificationResult(False, "indeterminate", "wrong evidence type for transition")
    if expected_source_revision is not None and evidence.source_revision != expected_source_revision:
        return VerificationResult(False, "indeterminate", "source revision mismatch")
    if not evidence.source.strip() or not evidence.source_revision.strip():
        return VerificationResult(False, "malformed", "missing evidence provenance")
    return VerificationResult(True, evidence.verdict, "evidence binding accepted")

```

## src/orion_v3/work_loop/policy.py

```python
"""Deterministic GREEN/YELLOW/RED classifier for Work Loop V1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import Proposal, RiskClass
from .paths import WorkspaceViolation, overlaps_frozen_path, require_inside_workspace


READ_ONLY_OPERATIONS = frozenset({"filesystem.read", "filesystem.list", "filesystem.search", "git.status", "git.diff"})
WORKSPACE_WRITE_OPERATIONS = frozenset({"filesystem.write", "filesystem.mkdir", "filesystem.delete", "git.add", "git.commit"})
RED_OPERATIONS = frozenset({"system.registry", "system.service", "system.shutdown", "credential.read", "policy.modify", "stop.modify"})


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    risk: RiskClass
    allowed_to_execute: bool
    reason: str


def _proposal_paths(proposal: Proposal) -> list[str]:
    values: list[str] = []
    for key in ("path", "paths", "destination", "source"):
        value = proposal.args.get(key)
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            values.extend(item for item in value if isinstance(item, str))
    return values


def classify_proposal(proposal: Proposal, frozen_paths: list[str] | None = None) -> PolicyDecision:
    frozen_paths = frozen_paths or []

    if proposal.requested_system_change or proposal.operation in RED_OPERATIONS:
        return PolicyDecision(RiskClass.RED, False, "system/authority operation is RED")

    try:
        for path in _proposal_paths(proposal):
            require_inside_workspace(path, proposal.workspace)
            if overlaps_frozen_path(path, proposal.workspace, frozen_paths):
                return PolicyDecision(RiskClass.RED, False, "target overlaps a frozen path")
    except WorkspaceViolation as exc:
        return PolicyDecision(RiskClass.RED, False, str(exc))

    if proposal.requested_install or proposal.requested_network:
        return PolicyDecision(RiskClass.YELLOW, False, "install/network requires owner decision")

    if proposal.operation in READ_ONLY_OPERATIONS:
        return PolicyDecision(RiskClass.GREEN, True, "bounded read-only operation")

    if proposal.operation in WORKSPACE_WRITE_OPERATIONS:
        return PolicyDecision(RiskClass.GREEN, True, "bounded workspace operation")

    return PolicyDecision(RiskClass.YELLOW, False, "unknown operation requires owner decision")

```

## src/orion_v3/work_loop/vault.py

```python
"""Minimal project Vault: STATE.md + append-only JOURNAL.md.

The Vault is project continuity, not ORION Memory.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import json

from .contracts import EvidenceRecord, WorkState


_STATE_MARKER = "<!-- ORION_WORK_STATE_V1 -->"


class VaultError(RuntimeError):
    pass


class ProjectVault:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve(strict=False)
        self.state_path = self.root / "STATE.md"
        self.journal_path = self.root / "JOURNAL.md"
        self.repo_path = self.root / "repo"

    def initialize(self, state: WorkState) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.repo_path.mkdir(exist_ok=True)
        if self.state_path.exists():
            raise VaultError("STATE.md already exists; refusing to overwrite project truth")
        self._write_state(state)
        if not self.journal_path.exists():
            self.journal_path.write_text("# Work Journal\n\n", encoding="utf-8")

    def load(self) -> WorkState:
        text = self.state_path.read_text(encoding="utf-8")
        marker = _STATE_MARKER + "\n"
        if marker not in text:
            raise VaultError("STATE.md is not an ORION Work State V1 file")
        payload = json.loads(text.split(marker, 1)[1])
        return WorkState(**payload)

    def record_verified_result(
        self,
        evidence: EvidenceRecord,
        *,
        next_action: str,
        blocked: bool | None = None,
    ) -> WorkState:
        current = self.load()
        if evidence.project_id != current.project_id or evidence.task_id != current.current_task:
            raise VaultError("evidence does not belong to current Vault task")
        updated = replace(
            current,
            last_verified_result=f"{evidence.evidence_type}:{evidence.verdict}",
            next_action=next_action,
            blocked=(evidence.verdict != "pass") if blocked is None else blocked,
        )
        self._write_state(updated)
        self.append_journal(
            f"{evidence.evidence_type.upper()} {evidence.verdict.upper()} "
            f"task={evidence.task_id} proposal={evidence.proposal_hash[:12]} "
            f"source={evidence.source}@{evidence.source_revision} {evidence.detail}".strip()
        )
        return updated

    def append_journal(self, entry: str) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        with self.journal_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(f"- {timestamp} — {entry}\n")

    def _write_state(self, state: WorkState) -> None:
        payload = json.dumps(
            {
                "project_id": state.project_id,
                "objective": state.objective,
                "checkpoint": state.checkpoint,
                "current_task": state.current_task,
                "last_verified_result": state.last_verified_result,
                "next_action": state.next_action,
                "blocked": state.blocked,
                "constraints": state.constraints,
                "frozen_paths": state.frozen_paths,
            },
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        rendered = (
            "# ORION Work State\n\n"
            "This file is canonical project continuity for the bounded Work project. "
            "It is not ORION Memory.\n\n"
            f"{_STATE_MARKER}\n{payload}\n"
        )
        temporary = self.state_path.with_suffix(".md.tmp")
        temporary.write_text(rendered, encoding="utf-8", newline="\n")
        temporary.replace(self.state_path)

```

## src/orion_v3/work_loop/paths.py

```python
"""Fail-closed workspace path checks.

These checks are pre-execution policy checks.  They are NOT a replacement for
OS-enforced sandboxing.  The physical sandbox gate remains mandatory.
"""

from __future__ import annotations

from pathlib import Path


class WorkspaceViolation(ValueError):
    pass


def resolved_workspace(path: str | Path) -> Path:
    root = Path(path).expanduser().resolve(strict=False)
    if not root.is_absolute():
        raise WorkspaceViolation("workspace must resolve to an absolute path")
    return root


def require_inside_workspace(candidate: str | Path, workspace: str | Path) -> Path:
    root = resolved_workspace(workspace)
    raw = Path(candidate).expanduser()
    target = raw if raw.is_absolute() else root / raw
    target = target.resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise WorkspaceViolation(f"path escapes workspace: {candidate}") from exc
    return target


def overlaps_frozen_path(
    candidate: str | Path, workspace: str | Path, frozen_paths: list[str]
) -> bool:
    target = require_inside_workspace(candidate, workspace)
    for frozen in frozen_paths:
        protected = require_inside_workspace(frozen, workspace)
        if target == protected or protected in target.parents or target in protected.parents:
            return True
    return False

```

## src/orion_v3/work_loop/contracts.py

```python
"""Typed contracts for the minimal Autonomous Work Loop V1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
import hashlib
import json
from typing import Any


class RiskClass(StrEnum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass(frozen=True, slots=True)
class Proposal:
    project_id: str
    task_id: str
    operation: str
    workspace: str
    args: dict[str, Any] = field(default_factory=dict)
    requested_network: bool = False
    requested_install: bool = False
    requested_system_change: bool = False

    def canonical_payload(self) -> bytes:
        return json.dumps(
            asdict(self), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

    @property
    def proposal_hash(self) -> str:
        return hashlib.sha256(self.canonical_payload()).hexdigest()


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    project_id: str
    task_id: str
    proposal_hash: str
    evidence_type: str
    verdict: str
    source: str
    source_revision: str
    detail: str = ""


@dataclass(slots=True)
class WorkState:
    project_id: str
    objective: str
    checkpoint: str
    current_task: str
    last_verified_result: str = "none"
    next_action: str = ""
    blocked: bool = False
    constraints: list[str] = field(default_factory=list)
    frozen_paths: list[str] = field(default_factory=list)

```

## src/orion_v3/work_loop/executor.py

```python
"""Execution boundary contract for a confined Work Hand.

No concrete executor is enabled until Windows workspace confinement physically
passes.  This prevents the staged foundation from becoming an unqualified
autonomous writer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .authorization import Authorization
from .contracts import EvidenceRecord, Proposal


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    proposal: Proposal
    authorization: Authorization


class WorkHandExecutor(Protocol):
    def execute(self, request: ExecutionRequest) -> EvidenceRecord:
        """Execute only after ORION authorization inside a qualified sandbox."""
        ...

```

## tests/test_work_loop_coordinator.py

```python
from orion_v3.work_loop.coordinator import WorkLoopCoordinator
from orion_v3.work_loop.contracts import Proposal, WorkState
from orion_v3.work_loop.vault import ProjectVault


class Stop:
    def __init__(self, active=False):
        self.active = active

    def stop_requested(self):
        return self.active


def make(tmp_path, stopped=False):
    vault = ProjectVault(tmp_path / "project")
    vault.initialize(WorkState(project_id="demo", objective="test", checkpoint="start", current_task="fix"))
    from orion_v3.work_loop.engine import WorkLoopEngine
    return WorkLoopCoordinator(WorkLoopEngine(vault), secret=b"test-only-secret", source_revision="fixture-rev", stop=Stop(stopped)), vault


def proposal(tmp_path, operation="filesystem.read", **flags):
    return Proposal("demo", "fix", operation, str(tmp_path / "project" / "repo"), **flags)


def test_green_dry_run_does_not_claim_pass(tmp_path):
    loop, vault = make(tmp_path)
    result = loop.cycle(proposal(tmp_path))
    assert result.status == "dry_run"
    assert result.evidence.verdict == "indeterminate"
    assert vault.load().last_verified_result == "execution:indeterminate"
    assert vault.load().blocked


def test_stop_blocks_cycle(tmp_path):
    loop, vault = make(tmp_path, stopped=True)
    assert loop.cycle(proposal(tmp_path)).status == "stopped"
    assert vault.load().last_verified_result == "none"


def test_red_denied(tmp_path):
    loop, vault = make(tmp_path)
    assert loop.cycle(proposal(tmp_path, operation="system.shutdown")).status == "denied"
    assert vault.load().last_verified_result == "none"


def test_yellow_requires_owner(tmp_path):
    loop, vault = make(tmp_path)
    assert loop.cycle(proposal(tmp_path, requested_network=True)).status == "awaiting_owner"
    assert vault.load().last_verified_result == "none"


def test_wrong_task_denied(tmp_path):
    loop, vault = make(tmp_path)
    p = Proposal("demo", "wrong", "filesystem.read", str(tmp_path / "project" / "repo"))
    assert loop.cycle(p).status == "denied"
    assert vault.load().last_verified_result == "none"


def test_stop_during_executor_prevents_state_commit(tmp_path):
    loop, vault = make(tmp_path)
    stop = loop.stop

    class StopDuringExecution:
        def execute(self, request):
            from orion_v3.work_loop.contracts import EvidenceRecord
            stop.active = True
            p = request.proposal
            return EvidenceRecord(p.project_id, p.task_id, p.proposal_hash,
                                  "execution", "indeterminate", "test-executor",
                                  "fixture-rev", "nothing executed")

    loop.executor = StopDuringExecution()
    outcome = loop.cycle(proposal(tmp_path))
    assert outcome.status == "stopped"
    assert vault.load().last_verified_result == "none"
    assert "nothing executed" not in vault.journal_path.read_text(encoding="utf-8")


def test_repeat_dry_run_never_records_pass(tmp_path):
    loop, vault = make(tmp_path)
    p = proposal(tmp_path)
    for _ in range(2):
        assert loop.cycle(p).status == "dry_run"
    assert vault.load().last_verified_result == "execution:indeterminate"
    assert vault.load().blocked is True

```

## tests/test_simulated_work_hand.py

```python
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from orion_v3.work_loop.authorization import issue_authorization
from orion_v3.work_loop.contracts import Proposal, RiskClass
from orion_v3.work_loop.executor import ExecutionRequest
from orion_v3.work_loop.simulated_hand import SimulatedWorkHand


def test_simulated_hand_accepts_exact_authorization_but_never_claims_pass(tmp_path):
    p = Proposal("p", "t", "filesystem.write", str(tmp_path))
    secret = b"test-secret"
    token = issue_authorization(p, RiskClass.GREEN, (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(), secret)
    hand = SimulatedWorkHand(secret=secret, source_revision="rev")
    result = hand.execute(ExecutionRequest(p, token))
    assert result.verdict == "indeterminate"
    assert result.source == "orion-simulated-work-hand"
    assert list(tmp_path.iterdir()) == []


def test_simulated_hand_rejects_changed_proposal(tmp_path):
    p = Proposal("p", "t", "filesystem.write", str(tmp_path))
    secret = b"test-secret"
    token = issue_authorization(p, RiskClass.GREEN, (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(), secret)
    changed = replace(p, operation="filesystem.delete")
    result = SimulatedWorkHand(secret=secret, source_revision="rev").execute(ExecutionRequest(changed, token))
    assert result.verdict == "fail"


def test_simulated_hand_rejects_expired_token(tmp_path):
    p = Proposal("p", "t", "filesystem.write", str(tmp_path))
    secret = b"test-secret"
    token = issue_authorization(p, RiskClass.GREEN, (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(), secret)
    result = SimulatedWorkHand(secret=secret, source_revision="rev").execute(ExecutionRequest(p, token))
    assert result.verdict == "fail"

```

## tests/test_calculator_simulation.py

```python
from orion_v3.work_loop.calculator_simulation import simulate_calculator_milestone


def test_calculator_simulation_is_blocked_until_real_executor():
    result = simulate_calculator_milestone()
    assert result == {
        "status": "dry_run",
        "evidence_verdict": "indeterminate",
        "last_verified_result": "execution:indeterminate",
        "blocked": "true",
        "source_written": "false",
    }

```