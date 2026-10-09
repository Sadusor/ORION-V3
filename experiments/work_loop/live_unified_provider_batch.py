"""Owner-triggered, bounded live provider smoke; proposals only, no execution."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parents[1]/"src"))
from live_two_cloud_architecture_demo import DONOR,runtime_from_existing_source
from orion_v3.work_loop.unified_cloud_adapter import dispatch,DispatchError

PROMPT=("Advisory only: propose three acceptance tests for a tiny offline Python "
        "SQLite task tracker. Plain text under 800 characters. Do not execute code.")
def main():
 if not (DONOR/"reviewer_connector.py").is_file():
  print("LIVE_ROUTER> DONOR_MISSING",flush=True);return 2
 sys.path.insert(0,str(DONOR))
 from provider_vault import ProviderVault
 from reviewer_connector import ReviewerConnector
 runtime=runtime_from_existing_source()
 connector=ReviewerConnector(runtime/"coding-mode"/"reviewers",
   provider_vault=ProviderVault(runtime/"provider-vault"),configured_free_providers=[])
 catalog=connector.refresh_catalog()
 models=[m for m in catalog.get("models",[]) if isinstance(m,dict)
         and m.get("available") is True and m.get("reviewer_id")
         and str(m.get("provider") or "").lower() in ("groq","gemini")
         and not any(x in str(m.get("model") or "").lower()
           for x in ("preview","audio","tts","whisper","guard","image","speech","live","transcribe"))]
 def priority(m):
  p=str(m.get("provider") or "").lower();name=str(m.get("model") or "").lower()
  return (0 if p=="groq" else 1,
          0 if "gpt-oss-120b" in name else 1 if "gpt-oss-20b" in name else 2 if "flash" in name else 3,name)
 models.sort(key=priority)
 chosen=[];providers=set()
 for m in models:
  p=str(m.get("provider") or "").lower()
  if p not in providers:
   chosen.append(m);providers.add(p)
  if len(chosen)>=2:break
 if not chosen:
  print("LIVE_ROUTER> NO_AVAILABLE_PROVIDER",flush=True);return 2
 success=0
 for m in chosen:
  p=str(m["provider"]).lower()
  print("LIVE_ROUTER> ATTEMPT",p,str(m.get("model") or "")[:75],flush=True)
  try:
   result=dispatch(provider=p,model=str(m.get("model") or ""),
       prompt=PROMPT,stop_requested=lambda:False,
       connector=connector,reviewer_id=m["reviewer_id"],timeout=45)
   output=result.get("text") or ""
   if not isinstance(output,str) or not output.strip():
    print("LIVE_ROUTER> EMPTY_RESPONSE",p,flush=True)
   else:
    success+=1
    print("LIVE_ROUTER> PASS",p,"CHARS",len(output),flush=True)
  except DispatchError as exc:
   print("LIVE_ROUTER> FAILED",p,"CATEGORY",exc.category,flush=True)
  except Exception as exc:
   print("LIVE_ROUTER> FAILED",p,"CLASS",type(exc).__name__,flush=True)
 print("LIVE_ROUTER> SUMMARY",success,"/",len(chosen),"NO_EXECUTION",flush=True)
 return 0 if success else 2
if __name__=="__main__":raise SystemExit(main())
