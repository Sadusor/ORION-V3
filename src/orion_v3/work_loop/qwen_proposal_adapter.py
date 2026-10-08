"""Strict replaceable Qwen proposal boundary. No model execution or tool authority."""
from __future__ import annotations

from dataclasses import fields
import json

from .contracts import Proposal
from .engine import WorkLoopEngine

MAX_RESPONSE_BYTES = 8192
ALLOWED = {f.name for f in fields(Proposal)}


def parse_qwen_proposal(raw: str, engine: WorkLoopEngine) -> Proposal:
    """Accept one JSON object only; bind project/task/workspace to canonical Vault."""
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise ValueError("Qwen response missing or exceeds 8 KiB")
    def no_duplicate(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    payload = json.loads(raw, object_pairs_hook=no_duplicate,
                         parse_constant=lambda value: (_ for _ in ()).throw(ValueError("non-finite JSON")))
    if not isinstance(payload, dict) or set(payload) != ALLOWED:
        raise ValueError("proposal schema mismatch")
    if any(type(payload[k]) is not bool for k in ("requested_network", "requested_install", "requested_system_change")):
        raise ValueError("risk flags must be boolean")
    if any(not isinstance(payload[k], str) or not payload[k] for k in ("project_id", "task_id", "operation", "workspace")):
        raise ValueError("proposal identity malformed")
    if not isinstance(payload["args"], dict):
        raise ValueError("proposal args must be object")
    state = engine.vault.load()
    if payload["project_id"] != state.project_id or payload["task_id"] != state.current_task:
        raise ValueError("Qwen cannot select another project or task")
    proposal = Proposal(**payload)
    proposal.canonical_payload()
    prepared = engine.prepare(proposal)
    if not prepared.policy.allowed_to_execute:
        raise ValueError(f"ORION policy blocked proposal: {prepared.policy.reason}")
    return proposal
