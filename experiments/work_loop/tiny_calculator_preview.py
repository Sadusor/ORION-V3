"""Tiny Calculator: an ORION-native, read-only proposal demonstration.

No cloud calls, subprocesses, source writes, authorization issuance, or execution.
The generated typed Proposal is intentionally submitted only to policy preparation.
"""
from __future__ import annotations
import json
from pathlib import Path
from orion_v3.work_loop.contracts import Proposal

PROJECT="tiny-calculator"
TASK="add-two-numbers"
SOURCE="""def add(a: int, b: int) -> int:
    return a + b
"""
TEST="""from calculator import add

def test_positive():
    assert add(2, 3) == 5

def test_negative():
    assert add(-4, 1) == -3
"""

def build_proposal(workspace: str) -> Proposal:
    return Proposal(project_id=PROJECT,task_id=TASK,
        operation="filesystem.write",workspace=workspace,
        args={"path":"calculator.py","content":SOURCE},
        requested_network=False,requested_install=False,requested_system_change=False)

def preview(workspace: str) -> dict:
    p=build_proposal(workspace)
    return {"project":PROJECT,"task":TASK,"proposal_hash":p.proposal_hash,
            "operation":p.operation,"workspace":p.workspace,
            "files_proposed":{"calculator.py":SOURCE,"test_calculator.py":TEST},
            "approval":"NOT_GRANTED","execution":"NOT_PERFORMED",
            "verification":"NOT_PERFORMED",
            "learning":"CANDIDATE_ONLY_NOT_PROMOTED"}

if __name__=="__main__":
    import sys
    workspace=sys.argv[1] if len(sys.argv)>1 else "E:/ORION-V3-EXPERIMENTS/tiny-calculator"
    print(json.dumps(preview(workspace),indent=2))
