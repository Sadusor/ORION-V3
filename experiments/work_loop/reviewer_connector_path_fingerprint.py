"""Read-only, privacy-safe AST fingerprint of connector mkdir path construction.

Emits operation structure, not identifiers, constants, paths or source.
"""
import ast
from pathlib import Path
SOURCE=Path("E:/ORION/spikes/coding_mode_github_loop/reviewer_connector.py")
def shape(n):
 if isinstance(n,ast.Name):return "NAME"
 if isinstance(n,ast.Constant):return "CONSTANT_"+type(n.value).__name__.upper()
 if isinstance(n,ast.Attribute):return "ATTRIBUTE("+shape(n.value)+")"
 if isinstance(n,ast.BinOp):return type(n.op).__name__.upper()+"("+shape(n.left)+","+shape(n.right)+")"
 if isinstance(n,ast.Call):return "CALL("+shape(n.func)+")"
 if isinstance(n,ast.Subscript):return "SUBSCRIPT("+shape(n.value)+")"
 if isinstance(n,ast.JoinedStr):return "FSTRING"
 return type(n).__name__.upper()
def main():
 if not SOURCE.is_file():
  print("CONNECTOR_PATH> SOURCE_MISSING",flush=True);return
 tree=ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
 for fn in (n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.lineno==527):
  for stmt in fn.body:
   if 550<=stmt.lineno<=563:
    if isinstance(stmt,(ast.Assign,ast.AnnAssign)):
     value=stmt.value
     print("CONNECTOR_PATH> ASSIGN",stmt.lineno,shape(value),flush=True)
    elif isinstance(stmt,ast.With):
     print("CONNECTOR_PATH> WITH",stmt.lineno,flush=True)
    elif isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Call):
     call=stmt.value
     if isinstance(call.func,ast.Attribute) and call.func.attr=="mkdir":
      print("CONNECTOR_PATH> MKDIR",stmt.lineno,"RECEIVER",shape(call.func.value),flush=True)
 print("CONNECTOR_PATH> READ_ONLY_COMPLETE",flush=True)
if __name__=="__main__":main()
