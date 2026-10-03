from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class CapabilityContractError(ValueError):
    """A semantic capability request violated the ORION contract."""


class CapabilityStatus(str, Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    PROVEN_ACTIVE = "PROVEN_ACTIVE"
    FROZEN_FALLBACK = "FROZEN_FALLBACK"
    RETIRED = "RETIRED"
    BLOCKED = "BLOCKED"


class EffectClass(str, Enum):
    READ_ONLY = "READ_ONLY"
    REVERSIBLE_ROUTINE = "REVERSIBLE_ROUTINE"
    BOUNDED_MODIFICATION = "BOUNDED_MODIFICATION"
    CONSEQUENTIAL = "CONSEQUENTIAL"


class ApprovalClass(int, Enum):
    READ_ONLY = 0
    REVERSIBLE_ROUTINE = 1
    BOUNDED_MODIFICATION = 2
    CONSEQUENTIAL = 3


@dataclass(frozen=True)
class ParameterSpec:
    kind: str
    required: bool = True
    default: Any = None
    enum: tuple[str, ...] = ()
    min_items: int | None = None
    max_items: int | None = None
    min_value: int | None = None
    max_value: int | None = None
    max_length: int | None = None

    def normalize(self, name: str, value: Any) -> Any:
        if value is None:
            if self.required:
                raise CapabilityContractError(f"{name} is required")
            return self.default

        if self.kind == "string":
            if not isinstance(value, str):
                raise CapabilityContractError(f"{name} must be a string")
            value = value.strip()
            if not value and self.required:
                raise CapabilityContractError(f"{name} must be non-empty")
            if self.max_length is not None and len(value) > self.max_length:
                raise CapabilityContractError(f"{name} exceeds max length")
            if self.enum and value not in self.enum:
                raise CapabilityContractError(f"{name} is not an allowed value")
            return value

        if self.kind == "bool":
            if not isinstance(value, bool):
                raise CapabilityContractError(f"{name} must be boolean")
            return value

        if self.kind == "int":
            if isinstance(value, bool) or not isinstance(value, int):
                raise CapabilityContractError(f"{name} must be an integer")
            if self.min_value is not None and value < self.min_value:
                raise CapabilityContractError(f"{name} is below minimum")
            if self.max_value is not None and value > self.max_value:
                raise CapabilityContractError(f"{name} exceeds maximum")
            return value

        if self.kind == "string_list":
            if not isinstance(value, list):
                raise CapabilityContractError(f"{name} must be an array")
            if self.min_items is not None and len(value) < self.min_items:
                raise CapabilityContractError(f"{name} has too few items")
            if self.max_items is not None and len(value) > self.max_items:
                raise CapabilityContractError(f"{name} has too many items")
            normalized: list[str] = []
            for item in value:
                if not isinstance(item, str) or not item.strip():
                    raise CapabilityContractError(f"{name} must contain non-empty strings")
                item = item.strip()
                if self.max_length is not None and len(item) > self.max_length:
                    raise CapabilityContractError(f"{name} item exceeds max length")
                if self.enum and item not in self.enum:
                    raise CapabilityContractError(f"{name} contains a disallowed value")
                normalized.append(item)
            return normalized

        raise CapabilityContractError(f"Unsupported parameter kind for {name}: {self.kind}")


@dataclass(frozen=True)
class CapabilityDefinition:
    capability_id: str
    version: int
    purpose: str
    status: CapabilityStatus
    parameters: Mapping[str, ParameterSpec]
    effect_class: EffectClass
    approval_class: ApprovalClass
    allowed_scopes: tuple[str, ...]
    binding_requirements: tuple[str, ...]
    implementation_candidates: tuple[str, ...]
    active_implementation: str | None
    availability_probe: str
    preconditions: tuple[str, ...]
    stop_contract: str
    evidence_contract: tuple[str, ...]
    postconditions: tuple[str, ...]
    provenance: str
    validated_sha: str | None
    physical_evidence_refs: tuple[str, ...]

    def normalize_params(self, params: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(params, Mapping):
            raise CapabilityContractError("params must be an object")

        unknown = set(params) - set(self.parameters)
        if unknown:
            raise CapabilityContractError(
                "Unknown parameter(s): " + ", ".join(sorted(unknown))
            )

        normalized: dict[str, Any] = {}
        for name, spec in self.parameters.items():
            normalized[name] = spec.normalize(name, params.get(name))
        return normalized


@dataclass(frozen=True)
class CapabilityProposal:
    intent: str | None
    params: Mapping[str, Any]
    ambiguity: str | None = None


@dataclass(frozen=True)
class ResolvedCapability:
    definition: CapabilityDefinition
    params: Mapping[str, Any]


_MODEL_PROPOSAL_KEYS = frozenset({"intent", "params", "ambiguity"})


def parse_model_proposal(payload: Mapping[str, Any]) -> CapabilityProposal:
    if not isinstance(payload, Mapping):
        raise CapabilityContractError("Model proposal must be an object")

    unknown = set(payload) - _MODEL_PROPOSAL_KEYS
    if unknown:
        raise CapabilityContractError(
            "Model proposal contains forbidden/unknown field(s): "
            + ", ".join(sorted(unknown))
        )

    intent_raw = payload.get("intent")
    intent = None if intent_raw is None else str(intent_raw).strip()
    if intent == "":
        intent = None

    params = payload.get("params", {})
    if not isinstance(params, Mapping):
        raise CapabilityContractError("params must be an object")

    ambiguity_raw = payload.get("ambiguity")
    ambiguity = None if ambiguity_raw is None else str(ambiguity_raw).strip()
    if ambiguity == "":
        ambiguity = None

    if intent is None and ambiguity is None:
        raise CapabilityContractError("Proposal requires intent or ambiguity")
    if intent is not None and ambiguity is not None:
        raise CapabilityContractError("Proposal cannot contain both intent and ambiguity")

    return CapabilityProposal(intent=intent, params=dict(params), ambiguity=ambiguity)
