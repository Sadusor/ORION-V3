"""Safe, deterministic provider-health state transitions.

No network, credentials or implicit probes. Only externally verified probe outcomes
may mark a model callable; failure triggers cooldown, never fake success.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Health:
 provider:str
 model:str
 status:str="UNKNOWN"
 failures:int=0
 cooldown_until:int=0
 last_success:int=0

def update_health(state,*,outcome,now,backoff_seconds=60):
 if not isinstance(state,Health) or not state.provider or not state.model:
  raise ValueError("valid provider/model required")
 if not isinstance(now,int) or now<0 or not isinstance(backoff_seconds,int) or backoff_seconds<1:
  raise ValueError("invalid clock or backoff")
 if outcome=="SUCCESS":
  return Health(state.provider,state.model,"CALLABLE",0,0,now)
 if outcome in {"RATE_LIMIT","PROVIDER","TRANSPORT","OVERLOADED"}:
  failures=min(state.failures+1,8)
  wait=min(backoff_seconds*(2**(failures-1)),3600)
  return Health(state.provider,state.model,"COOLDOWN",failures,now+wait,state.last_success)
 if outcome in {"AUTH","NO_CREDENTIAL","REQUEST","MALFORMED_RESPONSE"}:
  return Health(state.provider,state.model,"UNAVAILABLE",state.failures+1,0,state.last_success)
 raise ValueError("unrecognized probe outcome")

def is_callable(state,*,now,max_age=86400):
 if not isinstance(state,Health) or not isinstance(now,int) or now<0:
  return False
 return state.status=="CALLABLE" and state.last_success>0 and now>=state.last_success and now-state.last_success<=max_age

def can_probe(state,*,now):
 if not isinstance(state,Health) or not isinstance(now,int) or now<0:return False
 return state.status!="COOLDOWN" or now>=state.cooldown_until
