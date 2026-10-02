from __future__ import annotations

import json
from typing import Any, Callable, Mapping

from orion_v3.authority import ActionLease, AuthorityDenied, AuthorityGateway, AuthorizedOperation
from orion_v3.evidence import EvidenceEnvelope, Outcome


def build_gate1_capability_policy(agent_id: str):
    """Create the only acceptable OpenJarvis capability posture for Gate 1."""

    from openjarvis.security.capabilities import CapabilityPolicy

    policy = CapabilityPolicy(default_deny=True)
    policy.grant(agent_id, "file:read", "orion_filesystem_search")
    return policy


def build_filesystem_search_tool(
    gateway: AuthorityGateway,
    dispatcher: Callable[[AuthorizedOperation], Mapping[str, Any]],
    *,
    lease_token: str | None = None,
):
    """Build one OpenJarvis proxy tool instance.

    The lease is captured privately on the tool instance, never exposed in the
    model-facing ToolSpec or argument schema. An unbound instance is useful as
    a deliberate bypass probe: it remains discoverable/invokable by Jarvis but
    must fail at the ORION Gateway before dispatcher invocation.

    A bound instance is ephemeral authority: ORION creates it only after
    issuing a lease for the current dispatch. This avoids thread-local/context
    propagation assumptions inside donor executors.
    """

    from openjarvis.core.types import ToolResult
    from openjarvis.tools._stubs import BaseTool, ToolSpec

    class OrionFilesystemSearchTool(BaseTool):
        tool_id = "orion_filesystem_search"
        is_local = True

        def __init__(self, token: str | None) -> None:
            self._orion_lease_token = token

        @property
        def spec(self) -> ToolSpec:
            return ToolSpec(
                name=self.tool_id,
                description=(
                    "Search exact filenames inside ORION-authorized local locations. "
                    "ORION supplies trust roots and authority out of band."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "exact_names": {"type": "array", "items": {"type": "string"}},
                        "locations": {"type": "array", "items": {"type": "string"}},
                        "recursive": {"type": "boolean"},
                        "max_depth": {"type": "integer"},
                        "max_results": {"type": "integer"},
                    },
                    "required": ["exact_names", "locations"],
                    "additionalProperties": False,
                },
                category="orion",
                required_capabilities=["file:read"],
            )

        def execute(self, **params: Any) -> ToolResult:
            try:
                authorized = gateway.authorize(
                    lease_token=self._orion_lease_token,
                    operation_id="filesystem.search",
                    arguments=params,
                )
            except AuthorityDenied as exc:
                return ToolResult(
                    tool_name=self.tool_id,
                    content="ORION authority denied filesystem.search.",
                    success=False,
                    metadata={"orion_denial_code": exc.code},
                )

            try:
                result = dict(dispatcher(authorized))
            except Exception as exc:
                return ToolResult(
                    tool_name=self.tool_id,
                    content="ORION Hand execution failed.",
                    success=False,
                    metadata={
                        "orion_lease_id": authorized.lease.lease_id,
                        "orion_error_type": type(exc).__name__,
                    },
                )

            return ToolResult(
                tool_name=self.tool_id,
                content=json.dumps(result, ensure_ascii=False, sort_keys=True),
                success=True,
                metadata={
                    "orion_lease_id": authorized.lease.lease_id,
                    "orion_operation_id": authorized.operation_id,
                    "orion_result": result,
                },
            )

    return OrionFilesystemSearchTool(lease_token)



def build_registered_filesystem_search_tool(
    gateway: AuthorityGateway,
    *,
    lease_token: str | None,
    trusted_roots: Mapping[str, Any],
):
    """Create ORION's missing search capability through OpenJarvis ToolRegistry.

    This is the V3.1 path. OpenJarvis owns registration and tool execution;
    ORION supplies only its authority object, ephemeral lease and trusted roots.
    """

    # Import registers the extension with the donor's ToolRegistry.
    import orion_v3.substrates.openjarvis_tools  # noqa: F401
    from openjarvis.core.registry import ToolRegistry

    return ToolRegistry.create(
        "orion_filesystem_search",
        gateway=gateway,
        lease_token=lease_token,
        trusted_roots=trusted_roots,
    )


def normalize_filesystem_search_evidence(
    *,
    lease: ActionLease,
    tool_result: Any,
) -> EvidenceEnvelope:
    """Normalize an OpenJarvis ToolResult into ORION-owned canonical evidence."""

    if not getattr(tool_result, "success", False):
        return EvidenceEnvelope(
            task_id=lease.task_id,
            lease_id=lease.lease_id,
            operation_id=lease.operation_id,
            implementation_id="openjarvis.tool.orion_filesystem_search.v1",
            outcome=Outcome.FAILED,
            result={},
            verifier="orion.openjarvis.filesystem_search.v1",
            error=str(getattr(tool_result, "content", "tool execution failed")),
        )

    metadata = getattr(tool_result, "metadata", {}) or {}
    if metadata.get("orion_lease_id") != lease.lease_id:
        raise RuntimeError("OpenJarvis result lease does not match ORION lease")
    if metadata.get("orion_operation_id") != lease.operation_id:
        raise RuntimeError("OpenJarvis result operation does not match ORION lease")

    result = metadata.get("orion_result")
    if not isinstance(result, Mapping):
        raise RuntimeError("OpenJarvis result lacks structured ORION result evidence")

    implementation_id = str(
        metadata.get(
            "orion_implementation_id",
            "openjarvis.tool.orion_filesystem_search.v1",
        )
    )
    if result.get("implementation_id") != implementation_id:
        raise RuntimeError("OpenJarvis result implementation identity mismatch")

    return EvidenceEnvelope(
        task_id=lease.task_id,
        lease_id=lease.lease_id,
        operation_id=lease.operation_id,
        implementation_id=implementation_id,
        outcome=Outcome.CONFIRMED,
        result=dict(result),
        verifier="orion.openjarvis.filesystem_search.v1",
    )
