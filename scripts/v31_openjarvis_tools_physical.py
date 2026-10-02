from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENJARVIS_SRC = ROOT / "external" / "OpenJarvis" / "src"
if not OPENJARVIS_SRC.exists():
    raise SystemExit("Pinned OpenJarvis donor is missing.")

sys.path.insert(0, str(OPENJARVIS_SRC))
sys.path.insert(0, str(ROOT / "src"))

# Load OpenJarvis built-ins, then ORION's one missing custom capability.
import openjarvis.tools  # noqa: F401
import orion_v3.substrates.openjarvis_tools  # noqa: F401

from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolCall
from openjarvis.tools._stubs import ToolExecutor

from orion_v3.authority import AuthorityGateway, LeaseAuthority
from orion_v3.substrates.openjarvis import (
    build_gate1_capability_policy,
    build_registered_filesystem_search_tool,
    normalize_filesystem_search_evidence,
)


# Donor-first invariant: these are built-ins and remain donor-owned.
assert ToolRegistry.contains("file_read")
assert ToolRegistry.contains("file_write")

# Only filesystem.search is missing upstream, so ORION adds exactly one
# OpenJarvis-native custom tool.
assert ToolRegistry.contains("orion_filesystem_search")

leases = LeaseAuthority()
gateway = AuthorityGateway(leases)
issued = leases.issue(
    task_id="V3-RUN-002",
    operation_id="filesystem.search",
    principal="owner",
    scope={
        "locations": ["project"],
        "recursive": True,
        "max_depth": 4,
        "max_results": 10,
    },
    ttl_seconds=60,
)

tool = build_registered_filesystem_search_tool(
    gateway,
    lease_token=issued.token,
    trusted_roots={"project": ROOT},
)

agent_id = "orion-v31-openjarvis-tools"
policy = build_gate1_capability_policy(agent_id)
executor = ToolExecutor(
    [tool],
    capability_policy=policy,
    agent_id=agent_id,
)

call = ToolCall(
    id="V3-RUN-002-search",
    name=tool.tool_id,
    arguments=json.dumps(
        {
            "exact_names": ["pyproject.toml", "gateway.py"],
            "locations": ["project"],
            "recursive": True,
            "max_depth": 4,
            "max_results": 10,
        }
    ),
)
result = executor.execute(call)
assert result.success is True, result

payload = result.metadata["orion_result"]
paths = {item["relative_path"] for item in payload["matches"]}
assert "pyproject.toml" in paths, paths
assert "src/orion_v3/authority/gateway.py" in paths, paths

serialized = json.dumps(payload, sort_keys=True)
assert str(ROOT) not in serialized, "absolute ORION trusted root leaked"

evidence = normalize_filesystem_search_evidence(
    lease=issued.lease,
    tool_result=result,
)
assert evidence.task_id == "V3-RUN-002"
assert evidence.outcome.value == "confirmed"
assert evidence.result["match_count"] >= 2

print("V3_RUN_ID=V3-RUN-002")
print("OPENJARVIS_FILE_READ_BUILTIN=FOUND")
print("OPENJARVIS_FILE_WRITE_BUILTIN=FOUND")
print("OPENJARVIS_CUSTOM_SEARCH_REGISTERED=PASS")
print("REAL_FILESYSTEM_SEARCH=PASS")
print("ABSOLUTE_TRUST_ROOT_HIDDEN=PASS")
print("ORION_EVIDENCE_NORMALIZED=PASS")
print("V31_OPENJARVIS_TOOLS=PASS")
