"""Offline four-slot council coordinator; distinct families, STOP and proposal-only.

Slots are sequential to avoid connector state collisions. Reviewer output never
becomes an instruction to execute or an owner approval.
"""
from .free_council_slot import run_slot

SLOTS=("author_a","author_b","reviewer_a","reviewer_b")

def run_four(*, pools, invoke, stop_requested, task_id, checkpoint_path=None,
             max_attempts=4):
    if not callable(invoke) or not callable(stop_requested):
        raise ValueError("callbacks required")
    if not isinstance(task_id,str) or not task_id.strip():
        raise ValueError("task ID required")
    if set(pools)!=set(SLOTS):
        raise ValueError("exactly four council slots required")
    if not 1<=max_attempts<=8:
        raise ValueError("invalid attempt budget")
    completed={}
    reserved=set()
    for slot in SLOTS:
        if stop_requested():
            return {"status":"STOPPED","completed":completed}
        result=run_slot(candidates=pools[slot],invoke=lambda c:invoke(slot,c),
                        stop_requested=stop_requested,reserved_families=reserved,
                        checkpoint_path=checkpoint_path,task_id=task_id,
                        slot_id=slot,max_attempts=max_attempts)
        if result["status"]!="COMPLETED":
            return {"status":result["status"],"failed_slot":slot,
                    "completed":completed,"evidence":result["evidence"]}
        selected=result["selected"]
        if selected.family in reserved:
            raise RuntimeError("duplicate model family")
        reserved.add(selected.family)
        completed[slot]={"provider":selected.provider,"model":selected.model,
                         "family":selected.family,"text":result["result"]}
    return {"status":"PROPOSAL_ONLY_COMPLETE","completed":completed,
            "owner_approval":"NOT_GRANTED","execution":"NOT_PERFORMED"}
