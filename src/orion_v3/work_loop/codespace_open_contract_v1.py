"""CodeSpace open intent and provider-neutral work routing contracts.

Pure decisions only. Host/UI adapters must implement actual opening and report
observed success. Neither cloud models nor UI actions receive write authority.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

SCHEMA = "orion.codespace.request.v1"
OPEN_ACTION = "codespace.open"
_INTENTS = (
    r"^(?:qwen[,:]?\s*)?(?:please\s+)?open\s+(?:the\s+)?(?:code\s*space|coding workspace|coding window)(?:\s+for\s+(?:the\s+)?[\w.-]+)?[.!]?$",
    r"^(?:qwen[,:]?\s*)?(?:please\s+)?(?:let'?s|i want to)\s+(?:start\s+)?cod(?:e|ing)[.!]?$",
)
@dataclass(frozen=True, slots=True)
class CodeSpaceRequest:
    schema: str
    action: str
    project_id: str
    origin: str
    request_id: str
    can_execute: bool = False
    can_write: bool = False
    can_approve: bool = False

def recognize_codespace_open(message: str) -> bool:
    if not isinstance(message, str) or len(message) > 240:
        return False
    return any(re.fullmatch(p, message.strip(), re.IGNORECASE) for p in _INTENTS)

def request_codespace_open(*, project_id: str, origin: str, request_id: str,
                           authenticated: bool, stop_requested: bool) -> CodeSpaceRequest:
    if not authenticated or stop_requested:
        raise PermissionError("authenticated active session required")
    if origin not in {"qwen_chat", "pc_button", "android_qwen"}:
        raise ValueError("unsupported origin")
    if not isinstance(project_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", project_id):
        raise ValueError("invalid project")
    if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,96}", request_id):
        raise ValueError("invalid request id")
    return CodeSpaceRequest(SCHEMA, OPEN_ACTION, project_id, origin, request_id)

@dataclass(frozen=True, slots=True)
class CloudRole:
    provider: str
    model: str
    role: str
    free_tier: bool

def plan_coding_roles(*, coder: CloudRole, reviewer: CloudRole,
                      owner_approved_paid: bool, budget_remaining: bool) -> dict:
    for slot, expected in ((coder, "coder"), (reviewer, "reviewer")):
        if not isinstance(slot, CloudRole) or slot.role != expected or not slot.provider or not slot.model:
            raise ValueError("invalid role")
        if not slot.free_tier and not owner_approved_paid:
            raise PermissionError("paid model requires explicit owner authorization")
    if not budget_remaining:
        raise PermissionError("budget exhausted")
    if coder.provider == reviewer.provider and coder.model == reviewer.model:
        raise ValueError("independent reviewer required")
    return {"schema": "orion.codespace.cloud_roles.v1",
            "coder": {"provider": coder.provider, "model": coder.model},
            "reviewer": {"provider": reviewer.provider, "model": reviewer.model},
            "coordinator": "local_qwen",
            "can_execute": False, "can_write": False, "can_approve": False,
            "status": "ROUTING_PLAN_ONLY"}
