"""Bounded sequential fallback through unified adapter; proposal-only."""
from .free_provider_router import Candidate,Failure,select_next
from .unified_cloud_adapter import dispatch,DispatchError

def run_fallback(*,candidates,bindings,prompt,stop_requested,max_attempts=3):
    if not callable(stop_requested):raise ValueError("STOP callback required")
    if not isinstance(max_attempts,int) or not 1<=max_attempts<=4:raise ValueError("invalid budget")
    failures=[];events=[]
    for _ in range(max_attempts):
        c,reason=select_next(candidates=candidates,failures=failures,
            max_attempts=max_attempts,stop_requested=bool(stop_requested()))
        if c is None:
            return {"ok":False,"reason":reason,"events":events}
        key=(c.provider,c.model)
        binding=bindings.get(key)
        if not isinstance(binding,dict):
            category="NO_CREDENTIAL"
        else:
            try:
                result=dispatch(provider=c.provider,model=c.model,prompt=prompt,
                    stop_requested=stop_requested,**binding)
                if not isinstance(result,dict) or not isinstance(result.get("text"),str) or not result["text"].strip():
                    category="MALFORMED_RESPONSE"
                else:
                    events.append({"provider":c.provider,"model":c.model,"outcome":"SUCCESS"})
                    return {"ok":True,"result":result,"events":events}
            except DispatchError as exc:
                category=exc.category
            except Exception:
                category="UNCLASSIFIED"
        failures.append(Failure(c.provider,c.model,category))
        events.append({"provider":c.provider,"model":c.model,"outcome":category})
    return {"ok":False,"reason":"ATTEMPT_BUDGET_EXHAUSTED","events":events}
