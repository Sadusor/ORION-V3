"""Controlled single cloud proposal smoke via existing connector.

Explicit owner invocation only; no code execution, no automatic approval, no retries.
Never prints model output, prompts, credentials or provider errors.
"""
import argparse
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE.parents[1]/"src"))
from live_two_cloud_architecture_demo import DONOR,runtime_from_existing_source
from orion_v3.work_loop.existing_reviewer_slot_adapter import invoke_existing,ReviewerInvocationError

PROMPT=("ADVISORY ONLY. Propose three acceptance tests for a tiny offline Python "
        "SQLite task tracker. No code execution, no shell commands, no secrets. "
        "Respond in plain text under 1200 characters.")

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--confirm-live-proposal",action="store_true")
 parser.add_argument("--reviewer-id",default=None)
 parser.add_argument("--auto-gemini-flash",action="store_true")
 args=parser.parse_args()
 if not args.confirm_live_proposal:
  raise SystemExit("ORION_LIVE> NOT_AUTHORIZED")
 if not (DONOR/"reviewer_connector.py").is_file():
  raise SystemExit("ORION_LIVE> CONNECTOR_MISSING")
 sys.path.insert(0,str(DONOR))
 from provider_vault import ProviderVault
 from reviewer_connector import ReviewerConnector
 runtime=runtime_from_existing_source()
 connector=ReviewerConnector(runtime/"coding-mode"/"reviewers",
     provider_vault=ProviderVault(runtime/"provider-vault"),configured_free_providers=[])
 catalog=connector.refresh_catalog()
 models=[m for m in catalog.get("models",[]) if isinstance(m,dict) and m.get("available") is True]
 if args.auto_gemini_flash and not args.reviewer_id:
  choices=[m for m in models if str(m.get("provider") or "").lower()=="gemini"
           and "flash" in str(m.get("model") or "").lower()
           and not any(x in str(m.get("model") or "").lower()
                       for x in ("preview","image","tts","audio","live","thinking","lite"))]
  choices.sort(key=lambda m:(0 if "2.5-flash" in str(m.get("model") or "").lower() else 1,str(m.get("model") or "")))
  if not choices:raise SystemExit("ORION_LIVE> NO_STABLE_GEMINI_FLASH")
  args.reviewer_id=choices[0].get("reviewer_id")
 match=[m for m in models if m.get("reviewer_id")==args.reviewer_id
        and str(m.get("provider") or "").lower() in ("groq","gemini")]
 if len(match)!=1:raise SystemExit("ORION_LIVE> REVIEWER_NOT_AVAILABLE")
 print("ORION_LIVE> SELECTED_PROVIDER",str(match[0].get("provider") or "")[:30],flush=True)
 print("ORION_LIVE> SELECTED_MODEL",str(match[0].get("model") or "")[:100],flush=True)
 print("ORION_LIVE> START_PROPOSAL_ONLY",flush=True)
 try:
  output=invoke_existing(connector=connector,reviewer_id=args.reviewer_id,
        prompt=PROMPT,stop_requested=lambda:False,timeout=75)
 except ReviewerInvocationError as exc:
  print("ORION_LIVE> FAILURE_CATEGORY",exc.category,flush=True)
  try:
   state=connector.view()
   print("ORION_LIVE> CONNECTOR_STATE",str(state.get("state") or "unknown")[:40] if isinstance(state,dict) else "invalid",flush=True)
   entries=state.get("reviewers") or [] if isinstance(state,dict) else []
   if isinstance(entries,dict):entries=list(entries.values())
   if isinstance(entries,list):
    for entry in entries:
     if isinstance(entry,dict) and entry.get("reviewer_id")==args.reviewer_id:
      print("ORION_LIVE> REVIEWER_STATE",str(entry.get("state") or "unknown")[:40],flush=True)
      print("ORION_LIVE> REVIEWER_FIELD_NAMES",",".join(sorted(k for k in entry if k in {"state","output","error_code","status_code","failure_category","provider","model"})),flush=True)
  except Exception:
   print("ORION_LIVE> DIAGNOSTIC_UNAVAILABLE",flush=True)
  raise SystemExit(2)
 except Exception:
  print("ORION_LIVE> UNCLASSIFIED_CONNECTOR_FAILURE",flush=True)
  raise SystemExit(3)
 print("ORION_LIVE> SUCCESS_RESPONSE_CHARS",len(output),flush=True)
 print("ORION_LIVE> NO_EXECUTION_NO_APPROVAL",flush=True)
if __name__=="__main__":main()
