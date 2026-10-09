"""Inspect existing reviewer connector methods and credential sources, AST-only.

No secret reads, imports of donor connector, API calls, or credential values.
"""
import ast
from pathlib import Path
DONOR=Path("E:/ORION/spikes/coding_mode_github_loop")
METHODS={"start","view","stop","refresh_catalog"}
def main():
    for name in ("reviewer_connector.py","cloud_e2e_brainstorm_probe.py"):
        p=DONOR/name
        if not p.is_file():
            print("ORION_CONNECTOR_CONTRACT> MISSING",name,flush=True)
            continue
        tree=ast.parse(p.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in METHODS:
                args=[a.arg for a in node.args.args]
                print("ORION_CONNECTOR_CONTRACT> METHOD",node.name,"ARGS",",".join(args),flush=True)
        # Only named environment variable identifiers, never their values.
        envnames=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr in {"getenv","get"}:
                if node.args and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str):
                    label=node.args[0].value
                    if any(k in label.upper() for k in ("API","TOKEN","KEY","PROVIDER","ORION")):
                        envnames.add(label)
        print("ORION_CONNECTOR_CONTRACT> ENV_NAME_COUNT",len(envnames),flush=True)
        for label in sorted(envnames):
            print("ORION_CONNECTOR_CONTRACT> ENV_NAME",label[:90],flush=True)
    print("ORION_CONNECTOR_CONTRACT> AST_ONLY_NO_SECRETS_NO_INFERENCE",flush=True)
if __name__=="__main__":main()
