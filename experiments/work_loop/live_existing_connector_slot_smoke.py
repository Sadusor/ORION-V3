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
 parser.add_argument("--reviewer-id",required=True)
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
 match=[m for m in catalog.get("models",[]) if isinstance(m,dict)
        and m.get("reviewer_id")==args.reviewer_id and m.get("available") is True
        and str(m.get("provider") or "").lower() in ("groq","gemini")]
 if len(match)!=1:
  raise SystemExit("ORION_LIVE> REVIEWER_NOT_AVAILABLE")
 print("ORION_LIVE> START_PROPOSAL_ONLY",flush=True)
 try:
  output=invoke_existing(connector=connector,reviewer_id=args.reviewer_id,
        prompt=PROMPT,stop_requested=lambda:False,timeout=75)
 except ReviewerInvocationError as exc:
  print("ORION_LIVE> FAILURE_CATEGORY",exc.category,flush=True)
  raise SystemExit(2)
 except Exception:
  print("ORION_LIVE> UNCLASSIFIED_CONNECTOR_FAILURE",flush=True)
  raise SystemExit(3)
 print("ORION_LIVE> SUCCESS_RESPONSE_CHARS",len(output),flush=True)
 print("ORION_LIVE> NO_EXECUTION_NO_APPROVAL",flush=True)
if __name__=="__main__":main()
