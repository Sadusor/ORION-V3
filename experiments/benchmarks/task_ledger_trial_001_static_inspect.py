"""Read-only static inspection of saved cloud trial 001. Never imports or executes model text."""
from __future__ import annotations
import ast, hashlib, json, re
from pathlib import Path
from task_ledger_cloud_trial_001 import runtime_root

def inspect(text):
    fences=list(re.finditer(r"(?m)^\s*```([^\n]*)\n(.*?)^\s*```\s*$",text,re.S|re.M))
    print("LEDGER_INSPECT> FENCED_BLOCKS",len(fences),flush=True)
    candidates=[]
    for i,match in enumerate(fences,1):
        tag=match.group(1).strip()
        body=match.group(2)
        py=tag.lower() in ("python","py") or tag.lower().endswith(".py")
        syntax="N_A"
        if py:
            try:ast.parse(body);syntax="VALID"
            except SyntaxError:syntax="INVALID"
        candidates.append({"index":i,"tag":tag[:100],"chars":len(body),"python_syntax":syntax,
                           "sha256":hashlib.sha256(body.encode()).hexdigest()})
        print("LEDGER_INSPECT> BLOCK",i,"TAG",repr(tag[:70]),"CHARS",len(body),"SYNTAX",syntax,flush=True)
    package=bool(re.search(r"task_ledger[/\\]__main__\.py|task_ledger\.__main__",text,re.I))
    tests=len(re.findall(r"(?m)^\s*def\s+test_[A-Za-z0-9_]+\s*\(",text))
    imports=bool(re.search(r"(?m)^\s*(?:import|from)\s+",text))
    print("LEDGER_INSPECT> PACKAGE_ENTRYPOINT_MENTIONED",package,flush=True)
    print("LEDGER_INSPECT> TEST_FUNCTION_SIGNATURES_IN_RAW_TEXT",tests,flush=True)
    print("LEDGER_INSPECT> IMPORT_SYNTAX_PRESENT",imports,flush=True)
    print("LEDGER_INSPECT> STATIC_ONLY_NO_EXECUTION",flush=True)
    return {"fenced_blocks":candidates,"entrypoint_mentioned":package,"test_signatures":tests,
            "has_imports":imports,"inspection":"STATIC_ONLY","execution":"NOT_RUN",
            "completeness":"NOT_DETERMINED"}

def main():
    folder=runtime_root()/"coding-mode"/"reviewers"/"task-ledger-trial-001"
    path=folder/"cloud-output.txt"
    manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    data=path.read_text(encoding="utf-8")
    if len(data.encode("utf-8"))>1_000_000:raise RuntimeError("oversized saved response")
    # The producer hashes the Unicode response encoded as UTF-8 BEFORE write_text.\n    # On Windows, write_text may translate LF to CRLF on disk; read_text reverses it.\n    if hashlib.sha256(data.encode("utf-8")).hexdigest()!=manifest["output_sha256"]:\n        raise RuntimeError("saved output normalized-text hash mismatch")
    print("LEDGER_INSPECT> SAVED_OUTPUT_HASH_VERIFIED",flush=True)
    result=inspect(data)
    # Store only metadata; never extract or run model code.
    out=folder/"static-inspection.json"
    if out.exists():raise RuntimeError("inspection exists; refusing overwrite")
    out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print("LEDGER_INSPECT> METADATA_SAVED_PASS",flush=True)
if __name__=="__main__":main()
