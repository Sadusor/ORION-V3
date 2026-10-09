"""Pure capability-aware cloud candidate ranking, no credentials or API calls.

A catalog is not proof of callability. Eligibility requires explicit free-tier
confirmation, recent successful smoke and independent family attribution.
Private/paid keys must be explicitly opted into a separate reserve policy.
"""
from dataclasses import dataclass
from .free_provider_router import Candidate

@dataclass(frozen=True)
class ModelHealth:
    candidate: Candidate
    capability: str
    free_confirmed: bool
    smoke_passed: bool
    latency_ms: int
    quality: int
    cooldown: bool = False
    paid_or_private: bool = False

def rank_models(models, *, capability="coding", reserved_families=(),
                allow_private_reserve=False):
    if capability not in ("coding","review","planning"):
        raise ValueError("unsupported capability")
    eligible=[]
    for item in models:
        if not isinstance(item,ModelHealth):
            continue
        c=item.candidate
        if (item.capability!=capability or not c.provider or not c.model or not c.family
                or c.family in reserved_families or item.cooldown
                or not item.smoke_passed or not 0<=item.quality<=100
                or item.latency_ms<0):
            continue
        if item.paid_or_private:
            if not allow_private_reserve:continue
        elif not (c.free and item.free_confirmed):
            continue
        eligible.append(item)
    # Never silently prioritize a paid/private key above eligible free models.
    eligible.sort(key=lambda x:(int(x.paid_or_private),-x.quality,x.latency_ms,
                                x.candidate.provider,x.candidate.model))
    return tuple(x.candidate for x in eligible)
