from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENJARVIS_SRC = ROOT / "external" / "OpenJarvis" / "src"
sys.path.insert(0, str(OPENJARVIS_SRC))
sys.path.insert(0, str(ROOT / "src"))

from openjarvis.core.types import ToolCall
from openjarvis.tools._stubs import ToolExecutor
from orion_v3.authority import AuthorityGateway, LeaseAuthority
from orion_v3.hands import (
    FilesystemSearchHand,
    TrustedFilesystemRoots,
    normalize_search_evidence,
)
from orion_v3.substrates.openjarvis import (
    build_filesystem_search_tool,
    build_gate1_capability_policy,
)


leases = LeaseAuthority()
gateway = AuthorityGateway(leases)
hand = FilesystemSearchHand(TrustedFilesystemRoots({"project": ROOT}))

issued = leases.issue(
    task_id="v31-run-001",
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

captured = []


def dispatch(authorized):
    result = hand.execute(authorized)
    captured.append((authorized, result))
    return result


agent_id = "orion-v31-filesystem-search"
policy = build_gate1_capability_policy(agent_id)
tool = build_filesystem_search_tool(
    gateway,
    dispatch,
    lease_token=issued.token,
)
executor = ToolExecutor([tool], capability_policy=policy, agent_id=agent_id)

arguments = {
    "exact_names": ["pyproject.toml", "gateway.py"],
    "locations": ["project"],
    "recursive": True,
    "max_depth": 4,
    "max_results": 10,
}
result = executor.execute(
    ToolCall(
        id="v31-real-search",
        name=tool.tool_id,
        arguments=json.dumps(arguments),
    )
)

assert result.success is True, result
assert len(captured) == 1
authorized, hand_result = captured[0]
paths = {item["relative_path"] for item in hand_result["matches"]}
assert "pyproject.toml" in paths, paths
assert "src/orion_v3/authority/gateway.py" in paths, paths
assert str(ROOT) not in json.dumps(hand_result), "absolute trusted root leaked"

evidence = normalize_search_evidence(authorized, hand_result)
assert evidence.outcome.value == "confirmed"
assert evidence.task_id == "v31-run-001"
assert evidence.result["match_count"] >= 2

print("V3_RUN_ID=V3-RUN-001")
print("REAL_FILESYSTEM_SEARCH=PASS")
print("ABSOLUTE_TRUST_ROOT_HIDDEN=PASS")
print("NORMALIZED_EVIDENCE=PASS")
print("V31_FILESYSTEM_SEARCH=PASS")
