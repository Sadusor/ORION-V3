"""Bounded, owner-triggered free-model family preflight; never starts council.

One minimal text request per distinct family, max six attempts total.
Catalog listing is not proof of callability. No keys, prompts or response text
are saved. A passing probe is momentary, not a future quota guarantee.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
from orion_v3.work_loop.unified_cloud_adapter import dispatch,DispatchError
from live_four_family_council import free_openrouter_candidates

def probe(*, candidates, key, invoke=dispatch, limit=6):
    if not 1<=limit<=8:
        raise ValueError("invalid probe limit")
    families=set()
    attempted=[]
    seen=set()
    for candidate in candidates:
        family=candidate["family"]
        model=candidate["model"]
        if family in seen or len(attempted)>=limit or len(families)>=4:
            continue
        seen.add(family)
        if not model.endswith(":free"):
            continue
        try:
            response=invoke(provider="openrouter",model=model,
                prompt="Reply with exactly READY.",api_key=key,
                stop_requested=lambda:False,timeout=20)
            answer=response.get("text","")
            status="RESPONSIVE" if isinstance(answer,str) and answer.strip() else "EMPTY"
        except DispatchError as exc:
            status=exc.category
        except Exception:
            status="UNCLASSIFIED"
        attempted.append({"provider":"openrouter","model":model,
                          "family":family,"status":status})
        if status=="RESPONSIVE":
            families.add(family)
    return {"schema":"orion.v3.free-family-preflight.v1",
            "status":"FOUR_FAMILIES_RESPONSIVE" if len(families)>=4 else "INSUFFICIENT_RESPONSIVE_FAMILIES",
            "responsive_families":sorted(families),"attempts":attempted,
            "council_started":False,"owner_approval":"NOT_GRANTED",
            "execution":"NOT_PERFORMED"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    key=os.environ.get("OPENROUTER_API_KEY","").strip()
    if not key:
        print("PREFLIGHT> NO_CREDENTIAL",flush=True)
        return 2
    try:
        candidates=free_openrouter_candidates()
        result=probe(candidates=candidates,key=key)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open("x",encoding="utf-8") as stream:
            json.dump(result,stream,indent=2)
        for item in result["attempts"]:
            print("PREFLIGHT> FAMILY",item["family"],"MODEL",item["model"],
                  "STATUS",item["status"],flush=True)
        print("PREFLIGHT> RESULT",result["status"],"COUNT",
              len(result["responsive_families"]),flush=True)
        print("PREFLIGHT> EVIDENCE",args.output,flush=True)
        print("PREFLIGHT> NO_COUNCIL_NO_EXECUTION",flush=True)
        # A shortage is a valid preflight outcome, not a transport failure.
        return 0
    except Exception as exc:
        print("PREFLIGHT> ERROR",type(exc).__name__,flush=True)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
