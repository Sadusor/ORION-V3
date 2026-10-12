"""Cost-bounded model routing for coding council; no network or secrets here.

Transport is injected by trusted runtime. This adapter cannot itself call APIs.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from .role_contracts_v1 import Role

@dataclass(frozen=True, slots=True)
class ModelRoute:
    role: Role
    provider: str
    model: str
    max_output_tokens: int
    max_input_chars: int

@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: int
    output_tokens: int
    charged_usd: float

@dataclass(frozen=True, slots=True)
class ModelResponse:
    text: str
    usage: Usage

class BudgetedCouncilRouter:
    def __init__(self, *, routes: tuple[ModelRoute, ...],
                 transport: Callable[[ModelRoute, str, str], ModelResponse],
                 stop_requested: Callable[[], bool],
                 max_total_usd: float = 0.0, max_calls: int = 4):
        if not 1 <= max_calls <= 4 or not 0 <= max_total_usd <= 1:
            raise ValueError("invalid budget")
        if not callable(transport) or not callable(stop_requested):
            raise ValueError("trusted transport and STOP required")
        expected = {Role.GOVERNOR, Role.CODER, Role.REVIEWER}
        if len(routes) != 3 or {r.role for r in routes} != expected:
            raise ValueError("exactly three separate role routes required")
        if any(not r.provider or not r.model or not 1 <= r.max_output_tokens <= 4096
               or not 1 <= r.max_input_chars <= 16000 for r in routes):
            raise ValueError("invalid route limits")
        self.routes = {r.role: r for r in routes}
        self.transport = transport
        self.stop_requested = stop_requested
        self.max_total_usd = max_total_usd
        self.max_calls = max_calls
        self.calls = 0
        self.charged_usd = 0.0

    def invoke(self, role: Role, system: str, question: str) -> str:
        if self.stop_requested():
            raise ValueError("STOP active")
        if self.calls >= self.max_calls:
            raise ValueError("call budget exhausted")
        route = self.routes[Role(role)]
        if len(system) + len(question) > route.max_input_chars:
            raise ValueError("input exceeds route budget")
        # Conservative: charge each attempted request against call budget.
        self.calls += 1
        response = self.transport(route, system, question)
        if self.stop_requested():
            raise ValueError("STOP active")
        if not isinstance(response, ModelResponse):
            raise ValueError("missing trusted usage record")
        usage = response.usage
        if (not isinstance(usage, Usage) or type(usage.input_tokens) is not int
            or type(usage.output_tokens) is not int or usage.input_tokens < 0
            or usage.output_tokens < 0 or usage.output_tokens > route.max_output_tokens
            or not isinstance(usage.charged_usd, (int, float))
            or not 0 <= usage.charged_usd <= 1):
            raise ValueError("invalid usage")
        self.charged_usd += usage.charged_usd
        if self.charged_usd > self.max_total_usd:
            raise ValueError("spending cap exceeded; response rejected")
        if not isinstance(response.text, str) or not response.text.strip():
            raise ValueError("empty model response")
        return response.text
