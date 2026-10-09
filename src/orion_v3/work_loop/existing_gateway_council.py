"""Thin council-to-existing-gateway bridge. No new routing, no execution."""
from .four_slot_council import run_four, SLOTS
from .unified_cloud_adapter import dispatch, DispatchError
from .existing_reviewer_slot_adapter import ReviewerInvocationError
from .free_provider_router import Candidate
import hashlib
import json
from pathlib import Path

def run_gateway_council(*, candidates, credentials, connector, reviewer_ids,
                        task_id, objective, stop_requested, checkpoint_path=None, evidence_path=None):
    """All slots use the existing free router and provider dispatch.

    The caller supplies only confirmed-free candidates and explicit reviewer IDs.
    A completed council is advisory only; no automatic owner approval or execution.
    """
    if not isinstance(objective, str) or not objective.strip() or len(objective)>3000:
        raise ValueError("bounded objective required")
    if not isinstance(candidates,(tuple,list)) or any(
        not isinstance(c,Candidate) or not c.free or
        (c.provider=="openrouter" and not c.model.endswith(":free"))
        for c in candidates
    ):
        raise ValueError("confirmed-free candidates required")
    pools={slot:list(candidates) for slot in SLOTS}
    completed={}
    def invoke(slot,candidate):
        if stop_requested():
            raise ReviewerInvocationError("STOPPED")
        if slot.startswith("reviewer"):
            if "author_a" not in completed or "author_b" not in completed:
                raise ReviewerInvocationError("MALFORMED_RESPONSE")
            excerpts="\n".join(k+": "+completed[k][:1800] for k in ("author_a","author_b"))
            prompt="Critique BOTH independent designs, including security, tests, and disagreements. No execution.\n"+objective+"\n"+excerpts
        else:
            prompt="Independently propose modules, design, tests and risks. No execution.\n"+objective
        kwargs=({"api_key":credentials.get("openrouter")} if candidate.provider=="openrouter"
                else {"connector":connector,"reviewer_id":reviewer_ids.get((candidate.provider,candidate.model))})
        try:
            result=dispatch(provider=candidate.provider,model=candidate.model,
                            prompt=prompt,stop_requested=stop_requested,timeout=40,**kwargs)
        except DispatchError as exc:
            raise ReviewerInvocationError(exc.category) from None
        answer=result["text"]
        completed[slot]=answer
        return answer
    result=run_four(pools=pools,invoke=invoke,stop_requested=stop_requested,
                    task_id=task_id,checkpoint_path=checkpoint_path,max_attempts=4)
    if evidence_path is not None:
        entries=result.get("completed",{})
        evidence={
            "schema":"orion.v3.council.advisory.v1",
            "task_id":task_id,"objective":objective,"status":result["status"],
            "roles":{slot:{"provider":item["provider"],"model":item["model"],
                           "family":item["family"],"text":item["text"],
                           "sha256":hashlib.sha256(item["text"].encode("utf-8")).hexdigest()}
                     for slot,item in entries.items()},
            "owner_approval":"NOT_GRANTED","execution":"NOT_PERFORMED",
            "disagreements":"REQUIRES_OWNER_REVIEW",
        }
        destination=Path(evidence_path)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open("x",encoding="utf-8") as handle:
            json.dump(evidence,handle,indent=2,ensure_ascii=False)
    return result
