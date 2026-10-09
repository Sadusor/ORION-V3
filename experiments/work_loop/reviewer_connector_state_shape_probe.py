"""Read-only AST diagnostic of donor connector state and error classification.

Prints AST node shapes and allowlisted key names only, never literals containing
secrets, code snippets, exception messages or environment variable values.
"""
import ast
from pathlib import Path

SOURCE=Path("E:/ORION/spikes/coding_mode_github_loop/reviewer_connector.py")
METHODS={"start","view","stop"}
FIELDS={"state","status","reviewers","reviewer_id","output","error","error_code",
        "status_code","failure_category","provider","model","message","detail"}
def main():
 if not SOURCE.is_file():
  print("ORION_DIAG> SOURCE_MISSING",flush=True);return
 tree=ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
 for node in ast.walk(tree):
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in METHODS:
   keys=set()
   state_literals=set()
   for n in ast.walk(node):
    if isinstance(n,ast.Dict):
     for key in n.keys:
      if isinstance(key,ast.Constant) and isinstance(key.value,str) and key.value in FIELDS:
       keys.add(key.value)
    if isinstance(n,ast.Compare):
     for child in ast.walk(n):
      if isinstance(child,ast.Constant) and isinstance(child.value,str) and child.value.lower() in {
       "completed","complete","done","failed","failure","error","running","stopped",
       "cancelled","canceled","pending","success","finished"}:
       state_literals.add(child.value.lower())
   print("ORION_DIAG> METHOD",node.name,"DICT_FIELDS",",".join(sorted(keys)) or "none",flush=True)
   print("ORION_DIAG> METHOD",node.name,"COMPARED_STATES",",".join(sorted(state_literals)) or "none",flush=True)
 print("ORION_DIAG> AST_ONLY_NO_CREDENTIALS_NO_NETWORK",flush=True)
if __name__=="__main__":main()
