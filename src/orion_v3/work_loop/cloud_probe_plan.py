"""Bounded multi-provider probe planning without sending network requests.

Never infer API readiness from catalog entries. Caller must provide confirmed
free tier, provider identity, credential readiness and explicit probe approval.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class ProbeTarget:
 provider:str
 model:str
 family:str
 free_confirmed:bool
 credential_ready:bool
 capability:str="coding"
 private_key:bool=False

def plan_probes(targets,*,max_calls=3,allow_private=False,capability="coding"):
 if not isinstance(max_calls,int) or not 1<=max_calls<=8:
  raise ValueError("invalid probe budget")
 seen=set()
 families=set()
 selected=[]
 for t in targets:
  if not isinstance(t,ProbeTarget) or t.capability!=capability:
   continue
  if not (t.provider and t.model and t.family and t.credential_ready):
   continue
  if t.private_key:
   if not allow_private:continue
  elif not t.free_confirmed:
   continue
  key=(t.provider,t.model)
  if key in seen or t.family in families:continue
  selected.append(t)
  seen.add(key)
  families.add(t.family)
  if len(selected)==max_calls:break
 return tuple(selected)
