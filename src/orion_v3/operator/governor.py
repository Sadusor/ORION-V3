from __future__ import annotations

from typing import Any, Mapping

from orion_v3.capabilities import (
    ApprovalClass,
    CapabilityRegistry,
    CapabilityStatus,
    ParameterSpec,
    inherited_registry_v0,
)

from orion_v3.state import EventType, LocalEventExchange, OrionStateStore

from .control import OperatorControlDenied, OperatorControlPlane


_CAPABILITY_TOOL_PREFIX = "orion_capability_"
_CLOUD_TOOL = "orion_request_cloud_specialist"
_RESUME_TOOL = "orion_resume_approved_action"

# Model-facing semantic surface. Execution-policy knobs stay ORION-owned.
_GOVERNOR_PARAMETER_ALLOWLIST: dict[str, frozenset[str]] = {
    "fs.search_exact": frozenset({"exact_names", "locations"}),
}


def _governor_parameter_names(capability_id: str, definition) -> frozenset[str]:
    return _GOVERNOR_PARAMETER_ALLOWLIST.get(
        capability_id,
        frozenset(definition.parameters),
    )


def _tool_name(capability_id: str) -> str:
    return _CAPABILITY_TOOL_PREFIX + capability_id.replace(".", "__")


def _parameter_schema(spec: ParameterSpec) -> dict[str, Any]:
    if spec.kind == "string":
        schema: dict[str, Any] = {"type": "string"}
        if spec.enum:
            schema["enum"] = list(spec.enum)
        if spec.max_length is not None:
            schema["maxLength"] = spec.max_length
    elif spec.kind == "bool":
        schema = {"type": "boolean"}
    elif spec.kind == "int":
        schema = {"type": "integer"}
        if spec.min_value is not None:
            schema["minimum"] = spec.min_value
        if spec.max_value is not None:
            schema["maximum"] = spec.max_value
    elif spec.kind == "string_list":
        item_schema: dict[str, Any] = {"type": "string"}
        if spec.enum:
            item_schema["enum"] = list(spec.enum)
        if spec.max_length is not None:
            item_schema["maxLength"] = spec.max_length
        schema = {"type": "array", "items": item_schema}
        if spec.min_items is not None:
            schema["minItems"] = spec.min_items
        if spec.max_items is not None:
            schema["maxItems"] = spec.max_items
    else:
        raise ValueError("Unsupported governor parameter kind: " + spec.kind)

    if not spec.required:
        schema["default"] = spec.default
    return schema


def capability_tool_specs(
    registry: CapabilityRegistry | None = None,
) -> list[dict[str, Any]]:
    """Expose semantic ORION capabilities as proposal tools, never raw Hands."""
    registry = registry or inherited_registry_v0()
    specs: list[dict[str, Any]] = []

    for capability_id, definition in sorted(registry.snapshot().items()):
        if definition.status in {CapabilityStatus.BLOCKED, CapabilityStatus.RETIRED}:
            continue

        exposed_names = _governor_parameter_names(capability_id, definition)
        properties = {
            name: _parameter_schema(spec)
            for name, spec in definition.parameters.items()
            if name in exposed_names
        }
        required = [
            name
            for name, spec in definition.parameters.items()
            if name in exposed_names and spec.required
        ]
        if definition.approval_class.value >= ApprovalClass.BOUNDED_MODIFICATION.value:
            authority_note = (
                "ORION will freeze this exact proposal and create a human approval "
                "request. This tool never executes the underlying Hand."
            )
        else:
            authority_note = (
                "ORION will validate and record this proposal. This tool never "
                "executes the underlying Hand."
            )

        specs.append(
            {
                "type": "function",
                "function": {
                    "name": _tool_name(capability_id),
                    "description": (
                        definition.purpose
                        + " "
                        + authority_note
                        + " Use only when this registered capability exactly matches "
                        + "the owner's request."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                        "additionalProperties": False,
                    },
                },
            }
        )
    return specs


def governor_control_tool_specs(
    registry: CapabilityRegistry | None = None,
    *,
    include_resume: bool = True,
) -> list[dict[str, Any]]:
    tools = capability_tool_specs(registry)
    tools.append(
        {
            "type": "function",
            "function": {
                "name": _CLOUD_TOOL,
                "description": (
                    "Ask ORION to freeze and queue one difficult architecture, coding, "
                    "or review task for a cloud specialist. This creates a local Event "
                    "Exchange request only; it does not call a provider and grants the "
                    "specialist no execution authority."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "specialty": {
                            "type": "string",
                            "enum": ["architecture", "coding", "review"],
                        },
                        "task": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 20000,
                        },
                    },
                    "required": ["specialty", "task"],
                    "additionalProperties": False,
                },
            },
        }
    )
    if include_resume:
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": _RESUME_TOOL,
                    "description": (
                        "Resume one already-approved ORION action by approval id. "
                        "No replacement capability or parameters are accepted; ORION "
                        "returns only the exact action frozen before human approval."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "approval_id": {
                                "type": "string",
                                "minLength": 1,
                            }
                        },
                        "required": ["approval_id"],
                        "additionalProperties": False,
                    },
                },
            }
        )
    return tools


def pending_advisory_reviews(
    store: OrionStateStore,
    *,
    project_id: str,
    task_id: str,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Return normalized pending cloud REVIEW messages for the governor.

    Cloud response text is data, never authority. Any malformed/non-advisory
    exchange message addressed to the governor fails closed.
    """
    exchange = LocalEventExchange(store)
    messages = exchange.inbox(
        project_id,
        task_id,
        "orion:governor",
        limit=limit,
        pending_only=True,
    )
    reviews: list[dict[str, Any]] = []
    for message in messages:
        if message.event_type != EventType.REVIEW:
            raise OperatorControlDenied(
                "invalid_governor_review",
                "Governor inbox contained a non-REVIEW cloud response.",
            )
        body = dict(message.body)
        if body.get("kind") != "cloud_specialist_response":
            raise OperatorControlDenied(
                "invalid_governor_review",
                "Governor REVIEW has an unknown response kind.",
            )
        if body.get("authority") != "advisory_only":
            raise OperatorControlDenied(
                "invalid_governor_review_authority",
                "Cloud REVIEW is not explicitly advisory_only.",
            )
        required = (
            "request_id",
            "request_sha256",
            "specialty",
            "provider_id",
            "model_id",
            "response_text",
            "response_sha256",
        )
        missing = [name for name in required if not body.get(name)]
        if missing:
            raise OperatorControlDenied(
                "invalid_governor_review",
                "Cloud REVIEW missing field(s): " + ", ".join(missing),
            )
        reviews.append(
            {
                "event_id": message.event_id,
                "parent_event_id": message.parent_event_id,
                "request_id": body["request_id"],
                "request_sha256": body["request_sha256"],
                "specialty": body["specialty"],
                "provider_id": body["provider_id"],
                "model_id": body["model_id"],
                "response_text": body["response_text"],
                "response_sha256": body["response_sha256"],
                "authority": "advisory_only",
            }
        )
    return reviews


def acknowledge_advisory_review(
    store: OrionStateStore,
    *,
    project_id: str,
    event_id: str,
) -> None:
    """Record receipt only; acknowledgement never means acceptance/approval."""
    LocalEventExchange(store).acknowledge(
        project_id,
        event_id,
        "orion:governor",
    )


def dispatch_governor_tool(
    control: OperatorControlPlane,
    *,
    task_id: str,
    tool_name: str,
    arguments: Mapping[str, Any],
    actor_id: str,
) -> dict[str, Any]:
    """Deterministic model-facing control surface.

    The return value is authority/state information only. No Hand execution
    occurs here.
    """
    if tool_name.startswith(_CAPABILITY_TOOL_PREFIX):
        capability_id = tool_name[len(_CAPABILITY_TOOL_PREFIX):].replace("__", ".")
        definition = control.registry.get(capability_id)
        params = dict(arguments)
        exposed_names = _governor_parameter_names(capability_id, definition)
        hidden = set(params) - set(exposed_names)
        if hidden:
            raise OperatorControlDenied(
                "governor_hidden_parameter",
                "Model may not control ORION-owned execution parameter(s): "
                + ", ".join(sorted(hidden)),
            )

        if definition.approval_class.value >= ApprovalClass.BOUNDED_MODIFICATION.value:
            result = control.request_approval(
                task_id,
                capability_id=capability_id,
                params=params,
                requested_by=actor_id,
            )
            return {
                "kind": "approval_request",
                "status": result.approval.status.value,
                "duplicate": result.duplicate,
                "approval_id": result.approval.approval_id,
                "capability_id": result.approval.action.capability_id,
                "capability_version": result.approval.action.capability_version,
                "action_sha256": result.approval.action.action_sha256,
                "params": dict(result.approval.action.params),
            }

        proposal = control.propose_capability_action(
            task_id,
            capability_id=capability_id,
            params=params,
            proposed_by=actor_id,
        )
        return {
            "kind": "capability_proposal",
            "status": "PROPOSED",
            "event_id": proposal.event_id,
            "capability_id": proposal.action.capability_id,
            "capability_version": proposal.action.capability_version,
            "action_sha256": proposal.action.action_sha256,
            "approval_class": int(proposal.approval_class),
            "params": dict(proposal.action.params),
        }

    if tool_name == _CLOUD_TOOL:
        unknown = set(arguments) - {"specialty", "task"}
        if unknown:
            raise OperatorControlDenied(
                "unknown_governor_argument",
                "Unknown cloud-request argument(s): " + ", ".join(sorted(unknown)),
            )
        specialty = str(arguments.get("specialty") or "")
        task = str(arguments.get("task") or "")
        queued = control.queue_cloud_specialist(
            task_id,
            specialty=specialty,
            task=task,
            requested_by=actor_id,
        )
        return {
            "kind": "cloud_specialist_request",
            "status": "QUEUED",
            "duplicate": queued.duplicate,
            "request_id": queued.request.request_id,
            "specialty": queued.request.specialty,
            "task": queued.request.task,
            "request_sha256": queued.request.request_sha256,
            "recipient": queued.request.recipient,
            "event_id": queued.request.event_id,
        }

    if tool_name == _RESUME_TOOL:
        unknown = set(arguments) - {"approval_id"}
        if unknown:
            raise OperatorControlDenied(
                "unknown_governor_argument",
                "Resume accepts approval_id only.",
            )
        approval_id = str(arguments.get("approval_id") or "")
        if not approval_id:
            raise OperatorControlDenied(
                "approval_id_required",
                "approval_id is required for resume.",
            )
        consumed = control.consume_approved_action(
            approval_id,
            task_id=task_id,
            consumed_by=actor_id,
        )
        return {
            "kind": "approved_action_consumed",
            "status": consumed.approval.status.value,
            "approval_id": consumed.approval.approval_id,
            "capability_id": consumed.action.capability_id,
            "capability_version": consumed.action.capability_version,
            "action_sha256": consumed.action.action_sha256,
            "params": dict(consumed.action.params),
        }

    raise OperatorControlDenied(
        "unknown_governor_tool",
        "Unknown ORION governor control tool: " + tool_name,
    )
