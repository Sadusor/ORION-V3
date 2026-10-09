"""Owner-triggered live council using the existing gateway. Advisory only."""
import argparse
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
from orion_v3.work_loop.free_provider_router import Candidate
from orion_v3.work_loop.existing_gateway_council import run_gateway_council
from live_four_family_council import free_openrouter_candidates, existing_connector_candidates, TASK

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    key=os.environ.get("OPENROUTER_API_KEY","").strip()
    if not key:
        print("COUNCIL> MISSING_OPENROUTER_KEY",flush=True)
        return 2
    try:
        free=free_openrouter_candidates()
        private,connector=existing_connector_candidates()
        # The existing catalog may mark providers available without confirming
        # free entitlement. Only OpenRouter's zero-priced :free models are used
        # until each private provider is separately verified free.
        candidates=[Candidate("openrouter",c["model"],c["family"],True) for c in free]
        print("COUNCIL> ZERO_PRICED_FREE_CANDIDATES",len(candidates),flush=True)
        result=run_gateway_council(candidates=candidates,
            credentials={"openrouter":key},connector=connector,reviewer_ids={},
            task_id="first-task-tracker-advisory",objective=TASK,
            stop_requested=lambda:False,evidence_path=args.output,max_attempts=8)
        print("COUNCIL> STATUS",result["status"],"ROLES",len(result.get("completed",{})),flush=True)
        print("COUNCIL> FAILED_SLOT",result.get("failed_slot","NONE"),flush=True)
        for entry in result.get("evidence",()):
            print("COUNCIL> ATTEMPT",entry["provider"],entry["model"],entry["status"],flush=True)
        print("COUNCIL> EVIDENCE",args.output,flush=True)
        print("COUNCIL> OWNER_APPROVAL_NOT_GRANTED NO_EXECUTION",flush=True)
        return 0 if result["status"]=="PROPOSAL_ONLY_COMPLETE" else 2
    except Exception as exc:
        print("COUNCIL> FAILED",type(exc).__name__,flush=True)
        return 2
if __name__=="__main__":
    raise SystemExit(main())
