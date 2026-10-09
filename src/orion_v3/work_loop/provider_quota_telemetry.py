"""Parse allowlisted provider usage and rate-limit telemetry, never secrets."""
from .free_quota_monitor import classify, safe_record

def _integer(value):
    if isinstance(value,bool):return None
    if isinstance(value,int):return value if value>=0 else None
    if isinstance(value,str) and value.isascii() and value.isdecimal():
        return int(value[:16]) if len(value)<=16 else None
    return None

def _headers(headers):
    if headers is None:return {}
    if not isinstance(headers,dict):raise ValueError("headers must be dict")
    return {str(k).lower():str(v) for k,v in headers.items()
            if isinstance(k,str) and k.lower() in (
              "x-ratelimit-remaining-requests","x-ratelimit-remaining-tokens",
              "x-ratelimit-limit-tokens","retry-after",
              "x-ratelimit-reset-requests","x-ratelimit-reset-tokens")}

def observe(*,provider,model,response=None,headers=None,http_status=None,
            observed_at=None):
    """Returns safe summary. Missing quotas remain UNKNOWN, never unlimited.

    Header names are only interpreted for known Groq rate-limit conventions.
    Retry-After is a duration, NOT an absolute reset timestamp.
    """
    if response is not None and not isinstance(response,dict):
        raise ValueError("response must be dict")
    payload=response or {}
    usage=payload.get("usage")
    if not isinstance(usage,dict):usage={}
    total=_integer(usage.get("total_tokens"))
    if total is None:
        a=_integer(usage.get("prompt_tokens"))
        b=_integer(usage.get("completion_tokens"))
        if a is not None and b is not None:total=a+b
    safe_usage={"total_tokens":total} if total is not None else {}
    h=_headers(headers)
    quota={}
    if provider.lower()=="groq":
        for key,target in (
            ("x-ratelimit-remaining-requests","remaining_requests"),
            ("x-ratelimit-remaining-tokens","remaining_tokens"),
            ("x-ratelimit-limit-tokens","token_limit")):
            v=_integer(h.get(key))
            if v is not None:quota[target]=v
    snap=classify(provider=provider,model=model,usage=safe_usage,quota=quota,
                  rate_limited=http_status==429,observed_at=observed_at,
                  source="GROQ_RATE_HEADERS" if quota else
                  "PROVIDER_USAGE_ONLY" if safe_usage else "NOT_EXPOSED")
    record=safe_record(snap)
    retry=_integer(h.get("retry-after"))
    record["retry_after_seconds"]=min(retry,86400) if retry is not None else None
    record["prompt_tokens"]=_integer(usage.get("prompt_tokens"))
    record["completion_tokens"]=_integer(usage.get("completion_tokens"))
    return record
