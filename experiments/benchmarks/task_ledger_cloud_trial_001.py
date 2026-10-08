"""First single-cloud Task Ledger coding trial: existing ORION reviewer connector only.

Output is inert text; never execute generated code. No credentials printed or read here.
"""
from __future__ import annotations
import ast, hashlib, json, os, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DONOR=Path("E:/ORION/spikes/coding_mode_github_loop")
def runtime_root():
    tree=ast.parse((DONOR/"cloud_e2e_brainstorm_probe.py").read_text(encoding="utf-8-sig"))
    nodes=[n.value for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="runtime" for t in n.targets)]
    if len(nodes)!=1:raise RuntimeError("runtime contract changed")
    node=nodes[0];suffix=[]
    while isinstance(node,ast.BinOp) and isinstance(node.op,ast.Div):
        if not isinstance(node.right,ast.Constant) or not isinstance(node.right.value,str):raise RuntimeError("runtime suffix changed")
        suffix.insert(0,node.right.value);node=node.left
    if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name) or node.func.id!="Path":raise RuntimeError("runtime root changed")
    env=node.args[0]
    if not isinstance(env,ast.Call) or not isinstance(env.func,ast.Attribute) or env.func.attr!="get":raise RuntimeError("runtime env changed")
    path=Path(os.environ.get(env.args[0].value,str(Path.home())))
    for part in suffix:path=path/part
    return path

def main():
    contract=(ROOT/"docs/benchmarks/TASK_LEDGER_HTTP_CONTRACT_V01.md").read_text(encoding="utf-8")
    prompt=("Implement the following benchmark independently. Return source as inert text only. "
            "No tools, no execution, no claims of PASS. Provide a complete Python package and >=20 tests.\n\n"
            +task+"\n\n"+contract)
    # Connector's request bridge currently has a 4096-character prompt cap; check first.
    if len(prompt)>4096:raise RuntimeError("prompt exceeds existing reviewer bridge bound")
    sys.path.insert(0,str(DONOR))
    from provider_vault import ProviderVault
    from reviewer_connector import ReviewerConnector
    runtime=runtime_root()
    connector=ReviewerConnector(runtime/"coding-mode"/"reviewers",
                                provider_vault=ProviderVault(runtime/"provider-vault"),
                                configured_free_providers=[])
    catalog=connector.refresh_catalog()
    models=[m for m in catalog.get("models",[]) if isinstance(m,dict)
            and m.get("available") is True and m.get("reviewer_id")
            and str(m.get("provider") or "").lower() not in ("ollama","local","gemini")
            and "gpt-oss-120b" in str(m.get("model") or "").lower()]
    if not models:
        print("LEDGER_CLOUD> NOT_RUN_NO_ELIGIBLE_PROVIDER",flush=True)
        return
    chosen=models[0]
    print("LEDGER_CLOUD> MODEL",str(chosen.get("model") or "unknown")[:90],flush=True)
    print("LEDGER_CLOUD> PROMPT_SHA256",hashlib.sha256(prompt.encode()).hexdigest(),flush=True)
    started=time.monotonic()
    connector.start(prompt,[str(chosen["reviewer_id"])],popup_windows=False)
    state={}
    try:
        for _ in range(480):
            state=connector.view()
            if str(state.get("state") or "").lower() in ("completed","complete","failed","error","stopped"):break
            time.sleep(.25)
        else:
            connector.stop()
            print("LEDGER_CLOUD> TIMEOUT_NOT_SCORED",flush=True)
            return
        reviewers=state.get("reviewers") or []
        if isinstance(reviewers,dict):reviewers=list(reviewers.values())
        outputs=[x.get("output") for x in reviewers if isinstance(x,dict) and isinstance(x.get("output"),str) and x["output"].strip()]
        if not outputs:
            print("LEDGER_CLOUD> NO_OUTPUT_NOT_SCORED",flush=True)
            return
        output=outputs[0]
        # Store model text only under the pre-existing ORION runtime reviewer root.
        # Never write into the contender's executable workspace or print model content.
        target=runtime/"coding-mode"/"reviewers"/"task-ledger-trial-001"
        target.mkdir(parents=True,exist_ok=True)
        path=target/"cloud-output.txt"
        if path.exists():raise RuntimeError("trial output already exists; refusing overwrite")
        path.write_text(output,encoding="utf-8")
        manifest={"trial":"001","model":str(chosen.get("model") or "unknown"),
                  "prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),
                  "output_sha256":hashlib.sha256(output.encode()).hexdigest(),
                  "output_chars":len(output),"elapsed_seconds":round(time.monotonic()-started,2),
                  "execution":"NOT_RUN","independent_score":"NOT_RUN"}
        (target/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
        print("LEDGER_CLOUD> INERT_OUTPUT_SAVED",len(output),"CHARS",flush=True)
        print("LEDGER_CLOUD> NO_EXECUTION_NO_SCORE",flush=True)
    finally:
        if str(state.get("state") or "").lower() not in ("completed","complete","failed","error","stopped"):
            try:connector.stop()
            except Exception:pass
if __name__=="__main__":main()
