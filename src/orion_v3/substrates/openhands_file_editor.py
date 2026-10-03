from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from orion_v3.authority import AuthorityGateway
from orion_v3.evidence import EvidenceEnvelope, Outcome


_IMPLEMENTATION_ID = "openhands.file_editor.str_replace.v1"
_RESULT_START = "---ORION_OPENHANDS_RESULT_START---"
_RESULT_END = "---ORION_OPENHANDS_RESULT_END---"


class OpenHandsWorkerError(RuntimeError):
    pass


class OpenHandsSubprocessWorker:
    """Invoke the heavy OpenHands tool environment out of process."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not command:
            raise ValueError("worker command must not be empty")
        self._command = [str(x) for x in command]
        self._timeout_seconds = float(timeout_seconds)

    def __call__(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        try:
            proc = subprocess.run(
                self._command,
                input=json.dumps(dict(payload), ensure_ascii=False),
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise OpenHandsWorkerError("OpenHands worker timed out") from exc

        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise OpenHandsWorkerError(
                f"OpenHands worker exited with code {proc.returncode}: {detail[-1000:]}"
            )

        start = proc.stdout.find(_RESULT_START)
        end = proc.stdout.find(_RESULT_END)
        if start == -1 or end == -1 or end <= start:
            raise OpenHandsWorkerError("OpenHands worker result envelope missing")

        raw = proc.stdout[start + len(_RESULT_START) : end].strip()
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OpenHandsWorkerError("OpenHands worker returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise OpenHandsWorkerError("OpenHands worker result must be an object")
        return result


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def execute_openhands_file_replace(
    *,
    gateway: AuthorityGateway,
    lease_token: str | None,
    arguments: Mapping[str, Any],
    trusted_roots: Mapping[str, str | Path],
    worker: OpenHandsSubprocessWorker,
) -> EvidenceEnvelope:
    """Run one exact OpenHands FileEditor replacement under ORION authority."""

    authorized = gateway.authorize(
        lease_token=lease_token,
        operation_id="file.edit.replace",
        arguments=arguments,
    )
    args = authorized.arguments
    lease = authorized.lease

    location = str(args["location"])
    try:
        root = Path(trusted_roots[location]).expanduser().resolve()
    except KeyError as exc:
        raise RuntimeError(
            f"ORION trusted root binding missing for '{location}'"
        ) from exc
    if not root.exists() or not root.is_dir():
        raise RuntimeError(f"ORION trusted root '{location}' is unavailable")

    relative = PurePosixPath(str(args["relative_path"]))
    target = root.joinpath(*relative.parts).resolve()
    if target != root and not target.is_relative_to(root):
        raise RuntimeError("Resolved edit target escaped ORION trusted root")
    if not target.exists() or not target.is_file():
        return EvidenceEnvelope(
            task_id=lease.task_id,
            lease_id=lease.lease_id,
            operation_id=authorized.operation_id,
            implementation_id=_IMPLEMENTATION_ID,
            outcome=Outcome.FAILED,
            verifier="orion.openhands.file_edit.v1",
            error="Authorized target file does not exist.",
        )

    try:
        before = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return EvidenceEnvelope(
            task_id=lease.task_id,
            lease_id=lease.lease_id,
            operation_id=authorized.operation_id,
            implementation_id=_IMPLEMENTATION_ID,
            outcome=Outcome.FAILED,
            verifier="orion.openhands.file_edit.v1",
            error=f"Could not read authorized target: {type(exc).__name__}",
        )

    old_str = str(args["old_str"])
    new_str = str(args["new_str"])
    if before.count(old_str) != 1:
        return EvidenceEnvelope(
            task_id=lease.task_id,
            lease_id=lease.lease_id,
            operation_id=authorized.operation_id,
            implementation_id=_IMPLEMENTATION_ID,
            outcome=Outcome.FAILED,
            verifier="orion.openhands.file_edit.v1",
            error="old_str did not match exactly once before dispatch.",
        )

    expected_after = before.replace(old_str, new_str, 1)

    try:
        donor_result = worker(
            {
                "operation": "str_replace",
                "target_path": str(target),
                "old_str": old_str,
                "new_str": new_str,
            }
        )
    except OpenHandsWorkerError as exc:
        return EvidenceEnvelope(
            task_id=lease.task_id,
            lease_id=lease.lease_id,
            operation_id=authorized.operation_id,
            implementation_id=_IMPLEMENTATION_ID,
            outcome=Outcome.FAILED,
            verifier="orion.openhands.file_edit.v1",
            error=str(exc),
        )

    if donor_result.get("success") is not True:
        return EvidenceEnvelope(
            task_id=lease.task_id,
            lease_id=lease.lease_id,
            operation_id=authorized.operation_id,
            implementation_id=_IMPLEMENTATION_ID,
            outcome=Outcome.FAILED,
            verifier="orion.openhands.file_edit.v1",
            error="OpenHands FileEditor reported failure.",
        )

    try:
        after = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return EvidenceEnvelope(
            task_id=lease.task_id,
            lease_id=lease.lease_id,
            operation_id=authorized.operation_id,
            implementation_id=_IMPLEMENTATION_ID,
            outcome=Outcome.UNVERIFIABLE,
            verifier="orion.openhands.file_edit.v1",
            error=f"Could not verify edited target: {type(exc).__name__}",
        )

    if after != expected_after:
        return EvidenceEnvelope(
            task_id=lease.task_id,
            lease_id=lease.lease_id,
            operation_id=authorized.operation_id,
            implementation_id=_IMPLEMENTATION_ID,
            outcome=Outcome.UNVERIFIABLE,
            verifier="orion.openhands.file_edit.v1",
            error="Post-edit bytes do not match the authorized replacement.",
        )

    return EvidenceEnvelope(
        task_id=lease.task_id,
        lease_id=lease.lease_id,
        operation_id=authorized.operation_id,
        implementation_id=_IMPLEMENTATION_ID,
        outcome=Outcome.CONFIRMED,
        verifier="orion.openhands.file_edit.v1",
        result={
            "location": location,
            "relative_path": relative.as_posix(),
            "before_sha256": _sha256_text(before),
            "after_sha256": _sha256_text(after),
            "changed": before != after,
            "donor": "OpenHands FileEditor",
        },
    )


__all__ = [
    "OpenHandsSubprocessWorker",
    "OpenHandsWorkerError",
    "execute_openhands_file_replace",
]
