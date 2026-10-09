"""Fail-closed catalog candidate planning for the existing cloud reviewer connector.

No credentials, inference or execution. Unknown model families are excluded.
Catalog availability is not evidence of API callability or free-tier entitlement.
"""
from .free_provider_router import Candidate

def family_of(model):
    label=model.lower()
    if "gpt-oss" in label:return "gpt-oss"
    if "gemini" in label:return "gemini"
    if "qwen" in label:return "qwen"
    if "llama" in label:return "llama"
    if "gemma" in label:return "gemma"
    if "nemotron" in label:return "nemotron"
    return None

def plan_candidates(catalog, *, free_confirmed_ids=()):
    """Only explicitly confirmed free IDs can be considered for invocation."""
    confirmed=set(free_confirmed_ids)
    result=[]
    for item in catalog.get("models",[]):
        if not isinstance(item,dict) or item.get("available") is not True:continue
        identifier=item.get("reviewer_id")
        provider=str(item.get("provider") or "").lower()
        model=str(item.get("model") or "")
        family=family_of(model)
        if (not isinstance(identifier,str) or identifier not in confirmed or not family
                or provider not in {"groq","gemini","openrouter"}):continue
        if any(x in model.lower() for x in ("preview","tts","speech","guard","whisper","transcribe")):continue
        result.append((identifier,Candidate(provider,model,family,True)))
    return tuple(result)
