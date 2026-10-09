"""Bounded proposal-only council slot failover.

One independent slot per invocation; fallback never substitutes a reserved family.
No execution, credential storage, approval or implicit retries. Transport is injected.
"""
from .free_provider_router import Failure, select_next

def run_slot(*, candidates, invoke, stop_requested, reserved_families=(),
             cooldown_models=(), max_attempts=4):
    if not callable(invoke) or not callable(stop_requested):
        raise ValueError("callbacks required")
    failures = []
    evidence = []
    while True:
        candidate, reason = select_next(
            candidates=candidates, failures=failures,
            reserved_families=reserved_families,
            cooldown_models=cooldown_models, max_attempts=max_attempts,
            stop_requested=bool(stop_requested()))
        if candidate is None:
            return {"status":reason, "result":None, "evidence":tuple(evidence)}
        if stop_requested():
            return {"status":"STOPPED", "result":None, "evidence":tuple(evidence)}
        try:
            result = invoke(candidate)
        except Exception as exc:
            # Never persist exception strings: they may contain provider credentials.
            category = getattr(exc, "category", "UNCLASSIFIED")
            if not isinstance(category, str):
                category = "UNCLASSIFIED"
            failures.append(Failure(candidate.provider, candidate.model, category))
            evidence.append({"provider":candidate.provider,"model":candidate.model,
                             "family":candidate.family,"status":category})
            continue
        if stop_requested():
            return {"status":"STOPPED", "result":None, "evidence":tuple(evidence)}
        if not isinstance(result, str) or not result.strip() or len(result) > 16000:
            failures.append(Failure(candidate.provider,candidate.model,"MALFORMED_RESPONSE"))
            evidence.append({"provider":candidate.provider,"model":candidate.model,
                             "family":candidate.family,"status":"MALFORMED_RESPONSE"})
            continue
        evidence.append({"provider":candidate.provider,"model":candidate.model,
                         "family":candidate.family,"status":"COMPLETED"})
        return {"status":"COMPLETED", "result":result, "selected":candidate,
                "evidence":tuple(evidence)}
