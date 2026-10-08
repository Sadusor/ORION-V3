"""Five-provider council: reuse ORION's original configured reviewer connector."""
from __future__ import annotations
import ast
import os
import sys
import time
from pathlib import Path

donor=Path("E:/ORION/spikes/coding_mode_github_loop")
sys.path.insert(0,str(donor))
from provider_vault import ProviderVault
from reviewer_connector import ReviewerConnector

tree=ast.parse((donor/"cloud_e2e_brainstorm_probe.py").read_text(encoding="utf-8-sig"))
assign=[n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and
        any(isinstance(t,ast.Name) and t.id=="runtime" for t in n.targets)]
if len(assign)!=1: raise RuntimeError("runtime contract changed")
expr=assign[0]; parts=[]
while isinstance(expr,ast.BinOp) and isinstance(expr.op,ast.Div):
    if not isinstance(expr.right,ast.Constant) or not isinstance(expr.right.value,str):
        raise RuntimeError("runtime suffix changed")
    parts.insert(0,expr.right.value); expr=expr.left
if not isinstance(expr,ast.Call) or not isinstance(expr.func,ast.Name) or expr.func.id!="Path":
    raise RuntimeError("runtime root changed")
envcall=expr.args[0]
if not isinstance(envcall,ast.Call) or not isinstance(envcall.func,ast.Attribute) or envcall.func.attr!="get":
    raise RuntimeError("runtime environment changed")
runtime=Path(os.environ.get(envcall.args[0].value,str(Path.home())))
for part in parts: runtime=runtime/part
connector=ReviewerConnector(runtime/"coding-mode"/"reviewers",
                            provider_vault=ProviderVault(runtime/"provider-vault"),
                            configured_free_providers=[])
models=[m for m in connector.refresh_catalog().get("models",[]) if isinstance(m,dict)
        and m.get("available") is True and m.get("reviewer_id")
        and str(m.get("provider") or "").lower() not in ("ollama","local")]
def priority(m):
    s=(str(m.get("model") or "")+" "+str(m.get("provider") or "")).lower()
    return next((i for i,k in enumerate(("gpt-oss-120b","grok","deepseek","qwen","gemini")) if k in s),6)
models.sort(key=priority)
selected=[]; providers=set()
for m in models:
    p=str(m.get("provider") or "")
    if p not in providers:
        selected.append(m);providers.add(p)
    if len(selected)==5:break
for m in models:
    if len(selected)==5:break
    if m not in selected:selected.append(m)
print("M4_COUNCIL> AVAILABLE",len(models),"SELECTED",len(selected))
for i,m in enumerate(selected,1):
    print("M4_COUNCIL> MODEL",i,str(m.get("provider") or "")[:40],str(m.get("model") or "")[:80])
if len(selected)!=5:raise RuntimeError("five available cloud models required")
prompt=("ORION V3 architecture review: deterministic approval/policy authority, "
        "replaceable Windows execution hand, evidence Vault, and local Qwen 9B. "
        "Recommend three improvements for a low-power five-model review-and-synthesis "
        "loop, one failure mode and one measurable acceptance test. "
        "Advisory only: no tools, execution, credentials, or claimed PASS.")
connector.start(prompt,[str(m["reviewer_id"]) for m in selected],popup_windows=True)
print("M4_COUNCIL> FIVE_INDIVIDUAL_REVIEWER_WINDOWS_REQUESTED")\nprint("M4_COUNCIL> IDENTICAL_PROMPT_SENT_TO_FIVE")
deadline=time.monotonic()+110
try:
    while time.monotonic()<deadline:
        state=connector.view()
        if str(state.get("state") or "").lower() in ("completed","complete","error","failed","stopped"):
            break
        time.sleep(.5)
    else:
        print("M4_COUNCIL> TIMEOUT")
        raise RuntimeError("five-model council timeout")
    reviewers=state.get("reviewers") or []
    if isinstance(reviewers,dict):reviewers=list(reviewers.values())
    completed=0
    for i,x in enumerate(reviewers,1):
        if isinstance(x,dict):
            status=str(x.get("state") or "")
            has_output=bool(x.get("output"))
            print("M4_COUNCIL> RESULT",i,status,"HAS_OUTPUT",has_output)
            if status.lower() in ("completed","complete") and has_output:completed+=1
    print("M4_COUNCIL> RESPONSES_CONFIRMED",completed)
    print("M4_COUNCIL> QWEN_SYNTHESIS_REQUIRES_VERIFIED_OUTPUTS")
finally:
    try:
        if str(connector.view().get("state") or "").lower() not in ("completed","complete","error","failed","stopped"):
            connector.stop()
    except RuntimeError as exc:
        if "No active reviewer run" not in str(exc):raise
