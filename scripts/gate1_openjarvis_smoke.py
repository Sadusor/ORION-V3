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
agent_id = "orion-gate1-smoke"
policy = build_gate1_capability_policy(agent_id)

args = json.dumps(
    {
        "exact_names": ["report.txt"],
        "locations": ["documents"],
        "recursive": True,
        "max_depth": 2,
        "max_results": 5,
    }
)

# Falsifier 1: a discoverable but unbound proxy must remain unusable.
unbound_tool = build_filesystem_search_tool(gateway, fake_dispatch)
unbound_executor = ToolExecutor(
    [unbound_tool],
    capability_policy=policy,
    agent_id=agent_id,
)
denied = unbound_executor.execute(
    ToolCall(id="gate1-no-lease", name=unbound_tool.tool_id, arguments=args)
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

# Positive path: ORION creates an ephemeral lease-bound proxy instance.
bound_tool = build_filesystem_search_tool(
    gateway,
    fake_dispatch,
    lease_token=issued.token,
)
bound_executor = ToolExecutor(
    [bound_tool],
    capability_policy=policy,
    agent_id=agent_id,
)
allowed = bound_executor.execute(
    ToolCall(id="gate1-authorized", name=bound_tool.tool_id, arguments=args)
)

assert allowed.success is True, allowed
assert len(calls) == 1, calls
assert calls[0].lease.lease_id == issued.lease.lease_id

# Falsifier 2: model parameters cannot replace ORION-owned trust bindings.
scope_override_args = json.dumps(
    {
        "exact_names": ["report.txt"],
        "locations": ["documents"],
        "roots": {"documents": "C:/"},
    }
)
overridden = bound_executor.execute(
    ToolCall(
        id="gate1-scope-override",
        name=bound_tool.tool_id,
        arguments=scope_override_args,
    )
)
assert overridden.success is False, overridden
assert (
    overridden.metadata.get("orion_denial_code") == "trusted_binding_override"
), overridden
assert len(calls) == 1, "Trust-binding override reached dispatcher"

print("GATE1_OPENJARVIS_SMOKE=PASS")
print("NO_LEASE=DENIED")
print("AUTHORIZED_DISPATCH=PASS")
print("TRUST_BINDING_OVERRIDE=DENIED")
