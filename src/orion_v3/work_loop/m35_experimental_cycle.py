"""Experimental M3.5 coordinator: signed gate -> fixed native probe -> observer -> Vault.

The native fixture owns its own disposable workspace. This does NOT bind the
proposal's target path to the child, or qualify production STOP.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets
import subprocess
import time
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


def run_bound_experimental_cycle(base: Path, probe_dll: Path, revision: str, *, stop_requested, hold_for_stop_test=False) -> dict:
    """Experimental exact-target child, with trusted coordinator and independent byte check.

    STOP is sampled at boundaries; no claim of continuous production STOP.
    """
    import hashlib
    base = base.resolve(strict=True)
    probe_dll = probe_dll.resolve(strict=True)
    if base.drive.upper() != "E:" or not probe_dll.is_file() or not revision:
        raise ValueError("invalid bounded native execution")
    with TemporaryDirectory(prefix="ORION-M35-", dir=str(base)) as temp:
        root = Path(temp).resolve(strict=True)
        workspace = root / "ORION-M35-workspace"
        workspace.mkdir()
        vault = ProjectVault(root / "vault")
        # Windows cmd.exe produces CRLF. The signed bytes MUST match the child.
        content = "ORION M35 approved fixture\r\n"
        proposal = Proposal("orion-m35", "native-bound-write", "filesystem.write",
                            str(workspace), {"path": str(workspace / "approved.txt"),
                                             "content": content})
        vault.initialize(WorkState(project_id=proposal.project_id,
                                   objective="Prove exact-target native binding",
                                   checkpoint="M3.5-bound-experimental", current_task=proposal.task_id))
        secret = secrets.token_bytes(32)
        expiry = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
        auth = issue_authorization(proposal, RiskClass.GREEN, expiry, secret, source_revision=revision)
        from .m35_binding import bind_fixed_action
        # Separate bounded Windows CRLF contract: the signed proposal, not the child,
        # determines the expected exact file hash.
        from .authorization import verify_authorization
        from .policy import classify_proposal
        if (proposal.operation != "filesystem.write" or
            proposal.args["path"] != str(workspace / "approved.txt") or
            proposal.args["content"] != content or
            classify_proposal(proposal).risk != RiskClass.GREEN or
            not verify_authorization(auth, proposal, secret, expected_source_revision=revision)):
            raise RuntimeError("bound authorization rejected")
        expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if stop_requested():
            raise RuntimeError("STOP before bound native child")
        # Poll a live STOP source while the child runs. Kill on STOP/timeout;
        # this does not yet establish native descendant/Job Object termination.
        child_args = ["dotnet", str(probe_dll), str(workspace), expected]
        if hold_for_stop_test:
            child_args.append("--hold-for-stop-test")
        child = subprocess.Popen(child_args,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        deadline = time.monotonic() + 20
        try:
            while child.poll() is None:
                if stop_requested():
                    raise RuntimeError("STOP during bound native child")
                if time.monotonic() >= deadline:
                    raise RuntimeError("bound native child timeout")
                time.sleep(0.025)
            stdout, stderr = child.communicate(timeout=2)
        except BaseException:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)
            if hold_for_stop_test:
                pid_file = workspace / "stop_child_pid.txt"
                if not pid_file.is_file():
                    raise RuntimeError("STOP child PID was never observed")
                pid = int(pid_file.read_text(encoding="utf-8"))
                if pid <= 0:
                    raise RuntimeError("STOP child PID invalid")
                import os
                if os.name != "nt":
                    raise RuntimeError("STOP child liveness check requires Windows")
                import ctypes
                kernel = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
                kernel.OpenProcess.restype = ctypes.c_void_p
                kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
                kernel.WaitForSingleObject.restype = ctypes.c_ulong
                kernel.CloseHandle.argtypes = [ctypes.c_void_p]
                kernel.CloseHandle.restype = ctypes.c_int
                handle = kernel.OpenProcess(0x00100000, 0, pid)
                if handle:
                    try:
                        if kernel.WaitForSingleObject(handle, 5000) != 0:
                            raise RuntimeError("STOP native child remained running")
                    finally:
                        kernel.CloseHandle(handle)
                print("M35_STOP_TREE> NATIVE_CHILD_TERMINATED_AFTER_LAUNCHER_KILL", flush=True)
            raise
        print(stdout, end="", flush=True)
        if stderr:
            print(stderr, flush=True)
        required = ("M35_BOUND_ACTION> PASS_EXACT_BYTES_AT_AUTHORIZED_TARGET",
                    "OUTSIDE_READ> DENY", "OUTSIDE_WRITE> DENY",
                    "PROFILE_DELETE_HRESULT> 0x00000000")
        if child.returncode != 0 or any(x not in stdout for x in required):
            raise RuntimeError("bound native child failed")
        if stop_requested():
            raise RuntimeError("STOP after bound native child")
        target = workspace / "approved.txt"
        if not target.is_file() or target.read_bytes() != content.encode("utf-8"):
            raise RuntimeError("bound file exact bytes mismatch")
        if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            raise RuntimeError("bound file SHA256 mismatch")
        print("M35_BOUND_CYCLE> AUTHORIZED_TARGET_AND_BYTES_INDEPENDENTLY_VERIFIED", flush=True)
        evidence = EvidenceRecord(proposal.project_id, proposal.task_id,
                                  proposal.proposal_hash, "execution", "pass",
                                  "m35-bound-native-child", revision,
                                  "disposable exact-target byte match; continuous STOP unqualified")
        verified = verify_evidence(proposal, evidence, required_type="execution",
                                   expected_source_revision=revision)
        if not verified.accepted:
            raise RuntimeError("bound evidence rejected")
        vault.record_verified_result(evidence, next_action="Qualify production STOP",
                                     commit_guard=lambda: not stop_requested())
        if vault.load().last_verified_result != "execution:pass":
            raise RuntimeError("bound Vault readback failed")
        print("M35_BOUND_CYCLE> VAULT_EXECUTION_RECORDED_PASS", flush=True)
        return {"proposal_to_child": "experimental_pass",
                "exact_bytes": "pass", "vault": "pass",
                "production_stop": "not_qualified"}


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
