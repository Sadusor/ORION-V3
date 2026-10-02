from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OPENJARVIS_SRC = ROOT / "external" / "OpenJarvis" / "src"
if not OPENJARVIS_SRC.exists():
    raise SystemExit(
        "Pinned OpenJarvis donor is missing. Run scripts/fetch_openjarvis.ps1 first."
    )
sys.path.insert(0, str(OPENJARVIS_SRC))
sys.path.insert(0, str(ROOT / "src"))

from openjarvis.core.types import ToolCall
from openjarvis.tools._stubs import ToolExecutor
from orion_v3.authority import AuthorityGateway, LeaseAuthority
from orion_v3.substrates.openjarvis import (
    bind_action_lease,
    build_filesystem_search_tool,
    build_gate1_capability_policy,
)


calls = []


def fake_dispatch(authorized):
    calls.append(authorized)
    return {
        "status": "search_complete",
        "matches": [],
        "searched_locations": list(authorized.arguments["locations"]),
        "proof": "synthetic Gate-1 dispatcher; no filesystem side effect",
    }


leases = LeaseAuthority()
gateway = AuthorityGateway(leases)
tool = build_filesystem_search_tool(gateway, fake_dispatch)
agent_id = "orion-gate1-smoke"
policy = build_gate1_capability_policy(agent_id)
executor = ToolExecutor([tool], capability_policy=policy, agent_id=agent_id)

args = json.dumps(
    {
        "exact_names": ["report.txt"],
        "locations": ["documents"],
        "recursive": True,
        "max_depth": 2,
        "max_results": 5,
    }
)

# Falsifier 1: Jarvis can discover the proxy but cannot execute it without ORION authority.
denied = executor.execute(
    ToolCall(id="gate1-no-lease", name=tool.tool_id, arguments=args)
)
assert denied.success is False, denied
assert denied.metadata.get("orion_denial_code") == "missing_action_lease", denied
assert calls == [], "Dispatcher was reached without an ORION lease"

issued = leases.issue(
    task_id="gate1-task",
    operation_id="filesystem.search",
    principal="owner",
    scope={
        "locations": ["documents"],
        "recursive": True,
        "max_depth": 3,
        "max_results": 10,
    },
    ttl_seconds=60,
)

# Positive path: Jarvis and ORION must both allow before dispatcher is reached.
with bind_action_lease(issued.token):
    allowed = executor.execute(
        ToolCall(id="gate1-authorized", name=tool.tool_id, arguments=args)
    )

assert allowed.success is True, allowed
assert len(calls) == 1, calls
assert calls[0].lease.lease_id == issued.lease.lease_id

# Falsifier 2: a model cannot smuggle a trusted root through tool arguments.
attack_args = json.dumps(
    {
        "exact_names": ["report.txt"],
        "locations": ["documents"],
        "roots": {"documents": "C:/"},
    }
)
with bind_action_lease(issued.token):
    attacked = executor.execute(
        ToolCall(id="gate1-root-attack", name=tool.tool_id, arguments=attack_args)
    )
assert attacked.success is False, attacked
assert attacked.metadata.get("orion_denial_code") == "trusted_binding_override", attacked
assert len(calls) == 1, "Root-injection attack reached dispatcher"

print("GATE1_OPENJARVIS_SMOKE=PASS")
print("NO_LEASE=DENIED")
print("AUTHORIZED_DISPATCH=PASS")
print("TRUST_ROOT_INJECTION=DENIED")