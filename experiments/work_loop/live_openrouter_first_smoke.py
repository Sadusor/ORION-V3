"""Owner-approved OpenRouter-first live proposal smoke with bounded private fallback."""
import os,sys,json
from pathlib import Path
from urllib.request import Request,urlopen
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parents[1]/"src"))
from live_two_cloud_architecture_demo import DONOR,runtime_from_existing_source
from orion_v3.work_loop.unified_cloud_adapter import dispatch,DispatchError
PROMPT=("Advisory only. Give three acceptance tests for a tiny offline Python SQLite "
        "task tracker. Plain text under 800 characters. No code execution.")
def main():
 key=os.environ.get("OPENROUTER_API_KEY","").strip()
 if not key:
  print("OPENROUTER_FIRST> KEY_NOT_VISIBLE_TO_PROCESS",flush=True);return 2
 req=Request("https://openrouter.ai/api/v1/models",headers={"Accept":"application/json",
   "User-Agent":"ORION-V3-live-free-catalog"})
 try:
  with urlopen(req,timeout=20) as resp:payload=json.loads(resp.read(15000001))
 except Exception as exc:
  print("OPENROUTER_FIRST> CATALOG_FAILURE",type(exc).__name__,flush=True);return 2
 models=[]
 for m in payload.get("data",[]):
  if not isinstance(m,dict):continue
  name=m.get("id","");pricing=m.get("pricing") or {}
  if not isinstance(name,str) or not name.endswith(":free"):continue
  if str(pricing.get("prompt","")) not in ("0","0.0","0.000000") or str(pricing.get("completion","")) not in ("0","0.0","0.000000"):continue
  if any(s in name.lower() for s in ("image","audio","vision","guard","embed")):continue
  models.append(name)
 def priority(s):
  x=s.lower()
  return (0 if "qwen" in x else 1 if "gemma" in x else 2 if "nemotron" in x else 3,s)
 models.sort(key=priority)
 print("OPENROUTER_FIRST> FREE_CANDIDATES",len(models),flush=True)
 for model in models[:2]:
  print("OPENROUTER_FIRST> ATTEMPT",model[:100],flush=True)
  try:
   result=dispatch(provider="openrouter",model=model,prompt=PROMPT,
                   stop_requested=lambda:False,api_key=key,timeout=40)
   if isinstance(result,dict) and str(result.get("text") or "").strip():
    print("OPENROUTER_FIRST> PASS",model[:100],"CHARS",len(result["text"]),flush=True)
    print("OPENROUTER_FIRST> PRIVATE_APIS_NOT_USED",flush=True)
    return 0
  except DispatchError as exc:
   print("OPENROUTER_FIRST> FAILED_CATEGORY",exc.category,flush=True)
  except Exception as exc:
   print("OPENROUTER_FIRST> FAILED_CLASS",type(exc).__name__,flush=True)
 print("OPENROUTER_FIRST> FREE_ATTEMPTS_EXHAUSTED",flush=True)
 if not (DONOR/"reviewer_connector.py").is_file():
  print("OPENROUTER_FIRST> PRIVATE_FALLBACK_UNAVAILABLE",flush=True);return 2
 sys.path.insert(0,str(DONOR))
 from provider_vault import ProviderVault
 from reviewer_connector import ReviewerConnector
 runtime=runtime_from_existing_source()
 connector=ReviewerConnector(runtime/"coding-mode"/"reviewers",
    provider_vault=ProviderVault(runtime/"provider-vault"),configured_free_providers=[])
 rows=[m for m in connector.refresh_catalog().get("models",[]) if isinstance(m,dict)
       and m.get("available") is True and m.get("reviewer_id")
       and str(m.get("provider") or "").lower() in ("groq","gemini")
       and not any(x in str(m.get("model") or "").lower()
         for x in ("preview","audio","tts","image","whisper","guard","speech","transcribe"))]
 rows.sort(key=lambda m:(0 if str(m.get("provider")).lower()=="groq" else 1,
   0 if "gpt-oss-120b" in str(m.get("model","")).lower() else 1))
 if not rows:
  print("OPENROUTER_FIRST> NO_PRIVATE_FALLBACK",flush=True);return 2
 m=rows[0];provider=str(m["provider"]).lower()
 print("OPENROUTER_FIRST> FALLBACK_ATTEMPT",provider,str(m.get("model",""))[:100],flush=True)
 try:
  result=dispatch(provider=provider,model=str(m.get("model","")),prompt=PROMPT,
    stop_requested=lambda:False,connector=connector,reviewer_id=m["reviewer_id"],timeout=45)
  if not str(result.get("text") or "").strip():raise ValueError("empty")
  print("OPENROUTER_FIRST> FALLBACK_PASS",provider,"CHARS",len(result["text"]),flush=True)
  return 0
 except DispatchError as exc:
  print("OPENROUTER_FIRST> FALLBACK_FAILED",exc.category,flush=True)
 except Exception as exc:
  print("OPENROUTER_FIRST> FALLBACK_FAILED_CLASS",type(exc).__name__,flush=True)
 return 2
if __name__=="__main__":raise SystemExit(main())
