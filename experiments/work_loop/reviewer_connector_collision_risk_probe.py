"""Offline AST audit of connector session-name collision risk; no donor mutation.

Reports only time formatting precision, slice shape and path existence checks.
Does not print source, identifiers, string literals, paths or credentials.
"""
import ast
from pathlib import Path
SOURCE=Path("E:/ORION/spikes/coding_mode_github_loop/reviewer_connector.py")
def main():
 if not SOURCE.is_file():
  print("CONNECTOR_RISK> SOURCE_MISSING",flush=True);return
 tree=ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
 fn=next((n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.lineno==527),None)
 if fn is None:
  print("CONNECTOR_RISK> FUNCTION_CHANGED",flush=True);return
 for node in ast.walk(fn):
  if not 550<=getattr(node,"lineno",0)<=562:continue
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
   name=node.func.attr
   if name=="strftime":
    fmt=node.args[0] if node.args else None
    if isinstance(fmt,ast.Constant) and isinstance(fmt.value,str):
     f=fmt.value
     print("CONNECTOR_RISK> STRFTIME_PRECISION","MICROSECOND" if "%f" in f else "SECOND" if "%S" in f else "MINUTE_OR_COARSER",flush=True)
   if name in ("isoformat","time_ns","uuid4","token_hex","exists","is_dir"):
    print("CONNECTOR_RISK> OPERATION",name,flush=True)
  if isinstance(node,ast.Subscript) and node.lineno==559:
   sl=node.slice
   if isinstance(sl,ast.Slice):
    def bound(v):
     return "NONE" if v is None else "CONST_INT" if isinstance(v,ast.Constant) and isinstance(v.value,int) else type(v).__name__.upper()
    print("CONNECTOR_RISK> SLICE",bound(sl.lower),bound(sl.upper),bound(sl.step),flush=True)
   else:print("CONNECTOR_RISK> SUBSCRIPT_TYPE",type(sl).__name__,flush=True)
 print("CONNECTOR_RISK> READ_ONLY_COMPLETE",flush=True)
if __name__=="__main__":main()
