"""Pure OpenRouter catalog adapter: no HTTP, credentials, or execution."""
from .cloud_family_selection import family

def normalize_catalog(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError("invalid OpenRouter catalog")
    rows = []
    for item in payload["data"]:
        if not isinstance(item, dict):
            continue
        name = item.get("id")
        if not isinstance(name, str) or not name or len(name) > 200:
            continue
        group = family(name)
        if group == "unknown":
            continue
        pricing = item.get("pricing") or {}
        if not isinstance(pricing, dict):
            pricing = {}
        rows.append({"provider": "openrouter", "model": name, "reviewer_id": "openrouter:" + name,
                     "family": group, "available": True,
                     "context_length": item.get("context_length"),
                     "pricing_prompt": str(pricing.get("prompt") or ""),
                     "pricing_completion": str(pricing.get("completion") or "")})
    return rows
