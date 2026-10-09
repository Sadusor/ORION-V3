"""Deterministic, bounded free-provider fallback selection for ORION council slots.

No HTTP, credentials, shell, implicit model-family substitution or sleeping.
Caller owns execution, cooldown persistence, approval, and STOP.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Candidate:
    provider: str
    model: str
    family: str
    free: bool = True

@dataclass(frozen=True)
class Failure:
    provider: str
    model: str
    category: str

RECOVERABLE = frozenset({"RATE_LIMIT", "PROVIDER", "TRANSPORT", "OVERLOADED", "NO_CREDENTIAL"})
BLOCKING = frozenset({"STOPPED", "REQUEST", "MALFORMED_RESPONSE", "AUTH", "WRONG_ADAPTER"})

def select_next(*, candidates, failures=(), reserved_families=(), cooldown_models=(),
                max_attempts=4, stop_requested=False):
    """Return (candidate|None, reason); never cross council family boundaries."""
    if stop_requested:
        return None, "STOPPED"
    if not isinstance(max_attempts, int) or not 1 <= max_attempts <= 8:
        raise ValueError("invalid attempt budget")
    if len(failures) >= max_attempts:
        return None, "ATTEMPT_BUDGET_EXHAUSTED"
    if failures and failures[-1].category in BLOCKING:
        return None, "NON_RECOVERABLE"
    if failures and failures[-1].category not in RECOVERABLE:
        return None, "UNCLASSIFIED_FAILURE"
    tried = {(f.provider, f.model) for f in failures}
    reserved = set(reserved_families)
    cooling = set(cooldown_models)
    for c in candidates:
        if not c.free or not c.provider or not c.model or not c.family:
            continue
        if c.family in reserved or (c.provider, c.model) in tried or (c.provider, c.model) in cooling:
            continue
        return c, "SELECTED"
    return None, "NO_ELIGIBLE_FREE_CANDIDATE"
