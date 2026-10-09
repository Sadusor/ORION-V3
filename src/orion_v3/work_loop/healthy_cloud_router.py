"""Join measured provider health with free-first model ranking.

No network calls, no implicit paid API use, no fabricated availability.
"""
from dataclasses import replace
from .cloud_model_ranker import ModelHealth,rank_models
from .provider_health import Health,is_callable,can_probe

def rank_healthy(models,health_by_key,*,now,capability="coding",
                 reserved_families=(),allow_private_reserve=False,max_age=86400):
 if not isinstance(now,int) or now<0:
  raise ValueError("invalid time")
 ready=[]
 for item in models:
  if not isinstance(item,ModelHealth):continue
  key=(item.candidate.provider,item.candidate.model)
  health=health_by_key.get(key)
  if not isinstance(health,Health) or (health.provider,health.model)!=key:
   continue
  if not can_probe(health,now=now) or not is_callable(health,now=now,max_age=max_age):
   continue
  ready.append(replace(item,smoke_passed=True,cooldown=False))
 return rank_models(ready,capability=capability,reserved_families=reserved_families,
                    allow_private_reserve=allow_private_reserve)
