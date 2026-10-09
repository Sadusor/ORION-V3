"""Provider-neutral, read-only free-tier usage classification.

Never infer a remaining balance from successful calls or token usage.
Caller supplies verified quota data, if the provider actually exposes it.
"""
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class QuotaSnapshot:
    provider: str
    model: str
    status: str
    used_tokens: int | None
    remaining_tokens: int | None
    remaining_requests: int | None
    reset_at: str | None
    source: str
    observed_at: str

def _nonnegative(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0

def classify(*, provider, model, usage=None, quota=None, rate_limited=False,
             observed_at=None, source="NOT_EXPOSED", low_fraction=0.15):
    if not provider or not model or not 0 < low_fraction < 1:
        raise ValueError("invalid quota monitor input")
    if usage is not None and not isinstance(usage, dict):
        raise ValueError("invalid usage")
    if quota is not None and not isinstance(quota, dict):
        raise ValueError("invalid quota")
    usage = usage or {}
    quota = quota or {}
    used = usage.get("total_tokens")
    used = used if _nonnegative(used) else None
    remaining = quota.get("remaining_tokens")
    remaining = remaining if _nonnegative(remaining) else None
    requests = quota.get("remaining_requests")
    requests = requests if _nonnegative(requests) else None
    limit = quota.get("token_limit")
    limit = limit if _nonnegative(limit) and limit > 0 else None
    reset = quota.get("reset_at")
    reset = reset if isinstance(reset, str) and len(reset) <= 100 else None
    if rate_limited:
        status = "COOLDOWN"
    elif remaining == 0 or requests == 0:
        status = "EXHAUSTED"
    elif remaining is not None and limit is not None and remaining / limit <= low_fraction:
        status = "LOW"
    elif remaining is not None or requests is not None:
        status = "AVAILABLE"
    else:
        status = "UNKNOWN"
    stamp = observed_at or datetime.now(timezone.utc).isoformat()
    return QuotaSnapshot(str(provider), str(model), status, used, remaining,
                         requests, reset, str(source), stamp)

def safe_record(snapshot):
    """Safe-to-log metadata only; never API keys or raw provider payloads."""
    return {
        "provider": snapshot.provider, "model": snapshot.model,
        "status": snapshot.status, "used_tokens": snapshot.used_tokens,
        "remaining_tokens": snapshot.remaining_tokens,
        "remaining_requests": snapshot.remaining_requests,
        "reset_at": snapshot.reset_at, "source": snapshot.source,
        "observed_at": snapshot.observed_at,
    }
