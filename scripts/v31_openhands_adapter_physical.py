from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orion_v3.authority import AuthorityDenied, AuthorityGateway, LeaseAuthority
from orion_v3.evidence import Outcome
from orion_v3.substrates.openhands_file_editor import (
    OpenHandsSubprocessWorker,
    execute_openhands_file_replace,
)


SDK = ROOT / "external" / "OpenHands-software-agent-sdk"
WORKSPACE = ROOT / ".vendor" / "v3-run-009-openhands-adapter"
TARGET = WORKSPACE / "allowed.py"
OTHER = WORKSPACE / "other.py"

print("V3_RUN_ID> V3-RUN-009")
print("ORION_OPENHANDS_ADAPTER> START")

WORKSPACE.mkdir(parents=True, exist_ok=True)
TARGET.write_text(
    "VALUE = 1\n\ndef answer():\n    return VALUE\n",
    encoding="utf-8",
)
OTHER.write_text("OTHER = 1\n", encoding="utf-8")

leases = LeaseAuthority()
gateway = AuthorityGateway(leases)
issued = leases.issue(
    task_id="V3-RUN-009",
    operation_id="file.edit.replace",
    principal="owner",
    scope={
        "locations": ["project"],
        "relative_paths": ["allowed.py"],
        "max_replacement_chars": 1000,
    },
    ttl_seconds=90,
)

worker = OpenHandsSubprocessWorker(
    [
        "uv",
        "run",
        "--project",
        str(SDK),
        "--package",
        "openhands-tools",
        "python",
        str(ROOT / "scripts" / "v31_openhands_file_editor_worker.py"),
    ],
    timeout_seconds=30,
)

evidence = execute_openhands_file_replace(
    gateway=gateway,
    lease_token=issued.token,
    arguments={
        "location": "project",
        "relative_path": "allowed.py",
        "old_str": "VALUE = 1",
        "new_str": "VALUE = 2",
    },
    trusted_roots={"project": WORKSPACE},
    worker=worker,
)

assert evidence.outcome == Outcome.CONFIRMED, evidence
assert TARGET.read_text(encoding="utf-8").startswith("VALUE = 2")
serialized = json.dumps(dict(evidence.result), sort_keys=True)
assert str(WORKSPACE) not in serialized
assert str(TARGET) not in serialized

print("ORION_ACTION_LEASE_FILE_EDIT> ENFORCED")
print("OPENHANDS_ON_DEMAND_SUBPROCESS> PASS")
print("OPENHANDS_FILE_EDIT> PASS")
print("ORION_POST_EDIT_BYTE_VERIFICATION> PASS")
print("ORION_EVIDENCE_ENVELOPE> PASS")
print("ABSOLUTE_TRUST_ROOT_HIDDEN> PASS")

# Out-of-scope file must be denied by ORION before the donor worker is called.
try:
    execute_openhands_file_replace(
        gateway=gateway,
        lease_token=issued.token,
        arguments={
            "location": "project",
            "relative_path": "other.py",
            "old_str": "OTHER = 1",
            "new_str": "OTHER = 2",
        },
        trusted_roots={"project": WORKSPACE},
        worker=worker,
    )
except AuthorityDenied as exc:
    assert exc.code == "scope_violation", exc.code
else:
    raise AssertionError("Out-of-scope file edit unexpectedly authorized")

assert OTHER.read_text(encoding="utf-8") == "OTHER = 1\n"
print("OUT_OF_SCOPE_FILE_EDIT> DENIED_BEFORE_DONOR")

# Trust anchors remain private; model/request cannot replace them.
try:
    gateway.authorize(
        lease_token=issued.token,
        operation_id="file.edit.replace",
        arguments={
            "location": "project",
            "relative_path": "allowed.py",
            "old_str": "VALUE = 2",
            "new_str": "VALUE = 3",
            "repo_root": "C:/attacker-controlled",
        },
    )
except AuthorityDenied as exc:
    assert exc.code == "trusted_binding_override", exc.code
else:
    raise AssertionError("Trusted-root override unexpectedly authorized")

print("TRUSTED_BINDING_OVERRIDE> DENIED")
print("OPENHANDS_AGENT_LOOP> NONE")
print("ORION_OPENHANDS_ADAPTER> PASS")
print("STATUS> PASS")
