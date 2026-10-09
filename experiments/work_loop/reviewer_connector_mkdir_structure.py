"""Read-only structural inspection of the donor's mkdir(exist_ok=False) call.

Emits AST node types, assigned-variable relation and containing function line,
never raw expressions, string literals, source code, or absolute paths.
"""
import ast
from pathlib import Path
SOURCE=Path("E:/ORION/spikes/coding_mode_github_loop/reviewer_connector.py")
def main():
 if not SOURCE.is_file():
  print("CONNECTOR_MKDIR> SOURCE_MISSING",flush=True);return
 tree=ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
 for parent in ast.walk(tree):
  if not isinstance(parent,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
  for n in ast.walk(parent):
   if not isinstance(n,ast.Call) or not isinstance(n.func,ast.Attribute) or n.func.attr!="mkdir":continue
   if not any(k.arg=="exist_ok" and isinstance(k.value,ast.Constant) and k.value.value is False for k in n.keywords):continue
   print("CONNECTOR_MKDIR> FUNCTION_LINE",parent.lineno,"MKDIR_LINE",n.lineno,flush=True)
   receiver=n.func.value
   print("CONNECTOR_MKDIR> RECEIVER_TYPE",type(receiver).__name__,flush=True)
   for statement in parent.body:
    if n.lineno-22<=statement.lineno<=n.lineno+24:
     print("CONNECTOR_MKDIR> NEARBY",statement.lineno,type(statement).__name__,flush=True)
   for k in n.keywords:
    print("CONNECTOR_MKDIR> OPTION",k.arg,"VALUE_TYPE",type(k.value).__name__,flush=True)
 print("CONNECTOR_MKDIR> READ_ONLY_COMPLETE",flush=True)
if __name__=="__main__":main()
