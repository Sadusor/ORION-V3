"""Policy-only calculator demo; no filesystem writes or Hand execution."""
from __future__ import annotations
from dataclasses import replace
import json
from orion_v3.work_loop.contracts import RiskClass
from orion_v3.work_loop.policy import classify_proposal
from tiny_calculator_preview import build_proposal, preview

def run():
    workspace="E:/ORION-V3-EXPERIMENTS/tiny-calculator"
    proposal=build_proposal(workspace)
    cases={
        "calculator":classify_proposal(proposal,["protected.py"]),
        "path_escape":classify_proposal(replace(proposal,args={"path":"../outside.py","content":"x"}),["protected.py"]),
        "frozen_path":classify_proposal(replace(proposal,args={"path":"protected.py","content":"x"}),["protected.py"]),
        "network":classify_proposal(replace(proposal,requested_network=True),["protected.py"]),
    }
    expected={"calculator":RiskClass.GREEN,"path_escape":RiskClass.RED,
              "frozen_path":RiskClass.RED,"network":RiskClass.YELLOW}
    for name,decision in cases.items():
        assert decision.risk==expected[name],(name,decision)
    result=preview(workspace)
    result["policy_cases"]={name:{"risk":decision.risk.value,"reason":decision.reason}
                            for name,decision in cases.items()}
    print(json.dumps(result,indent=2))
    print("TINY_CALCULATOR> POLICY_CASES_PASS_4_OF_4")
    print("TINY_CALCULATOR> NO_HAND_NO_EXECUTION_NO_VAULT_WRITE")

if __name__=="__main__":run()
