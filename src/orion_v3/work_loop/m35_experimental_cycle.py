"""Experimental M3.5 coordinator: signed gate -> fixed native probe -> observer -> Vault.

The native fixture owns its own disposable workspace. This does NOT bind the
proposal's target path to the child, or qualify production STOP.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets
import subprocess
from tempfile import TemporaryDirectory

from .authorization import issue_authorization
from .contracts import EvidenceRecord, Proposal, RiskClass, WorkState
from .m35_preflight import validate_disposable_append
from .m35_binding import bind_fixed_action, authenticate_manifest, verify_manifest_mac
from .verifier import verify_evidence
from .vault import ProjectVault


REQUIRED = (
    "M35_FIXED_ACTION> PASS_APPCONTAINER_EXECUTED",
    "INSIDE_WRITE> ALLOW",
    "OUTSIDE_READ> DENY",
    "OUTSIDE_WRITE> DENY",
    "OUTSIDE_UNCHANGED> True",
    "PROFILE_DELETE_HRESULT> 0x00000000",
)


def run_experimental_cycle(base: Path, probe_dll: Path, revision: str, *, stop_requested) -> dict:
    """Only an owner-started fixed fixture; caller supplies STOP observation.

    Fail closed if STOP unavailable. The fixture is not a general executor.
    """
    base = base.resolve(strict=True)
    probe_dll = probe_dll.resolve(strict=True)
    if base.drive.upper() != "E:" or not probe_dll.is_file() or not revision:
        raise ValueError("invalid disposable fixture or revision")
    with TemporaryDirectory(prefix="ORION-M35-", dir=str(base)) as temp:
        root = Path(temp).resolve(strict=True)
        workspace = root / "ORION-M35-workspace"
        workspace.mkdir()
        vault = ProjectVault(root / "vault")
        proposal = Proposal("orion-m35", "fixed-native-fixture", "filesystem.write",
                            str(workspace), {"path": str(workspace / "approved.txt"),
                                             "content": "ORION M35 approved fixture\n"})
        vault.initialize(WorkState(project_id=proposal.project_id,
                                   objective="Prove bounded native fixture with verified evidence",
                                   checkpoint="M3.5-experimental", current_task=proposal.task_id))
        secret = secrets.token_bytes(32)
        expiry = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
        auth = issue_authorization(proposal, RiskClass.GREEN, expiry, secret, source_revision=revision)
        validate_disposable_append(proposal, auth, secret=secret,
                                   source_revision=revision, workspace=workspace)
        manifest = bind_fixed_action(proposal, revision)
        mac = authenticate_manifest(manifest, secret)
        if not verify_manifest_mac(manifest, secret, mac):
            raise RuntimeError("manifest authentication failed")
        if stop_requested():
            raise RuntimeError("STOP before fixture")
        print("M35_CYCLE> AUTHENTICATED_MANIFEST_PASS_NOT_NATIVE_ENFORCED", flush=True)
        print("M35_CYCLE> SIGNED_AUTHORIZATION_PASS", flush=True)
        # Existing native fixture creates and confines its OWN disposable path.
        # No user/model-controlled shell commands or file paths reach this child.
        result = subprocess.run(["dotnet", str(probe_dll)], capture_output=True,
                                text=True, timeout=20, check=False)
        print(result.stdout, end="", flush=True)
        if result.stderr:
            print(result.stderr, flush=True)
        if result.returncode != 0 or any(marker not in result.stdout for marker in REQUIRED):
            raise RuntimeError("native fixture evidence failed")
        print("M35_CYCLE> NATIVE_OBSERVATION_PASS", flush=True)
        if stop_requested():
            raise RuntimeError("STOP before Vault record")
        evidence = EvidenceRecord(proposal.project_id, proposal.task_id,
                                  proposal.proposal_hash, "manual", "pass",
                                  "m35-native-fixture", revision,
                                  "sandbox fixture qualification only; signed proposal target NOT executed")
        verified = verify_evidence(proposal, evidence, required_type="manual",
                                   expected_source_revision=revision)
        if not verified.accepted:
            raise RuntimeError("evidence binding rejected")
        vault.record_verified_result(evidence, next_action="Qualify proposal-to-child binding",
                                     commit_guard=lambda: not stop_requested())
        state = vault.load()
        if state.last_verified_result != "manual:pass":
            raise RuntimeError("Vault did not record verified fixture")
        if "MANUAL PASS" not in vault.journal_path.read_text(encoding="utf-8"):
            raise RuntimeError("Vault journal missing result")
        print("M35_CYCLE> VAULT_FIXTURE_RECORDED_PASS_NOT_PROPOSAL_EXECUTION", flush=True)
        return {"fixture": "pass", "vault": "pass", "proposal_to_child": "not_qualified",
                "production_stop": "not_qualified"}
