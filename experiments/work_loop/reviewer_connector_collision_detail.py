"""Safe read-only AST analysis of exclusive-create and connector start lifecycle.

Emits only operation type, source line, and AST context (function/class name).
No source code, literal strings, paths, identifiers or credentials are printed.
"""
import ast
from pathlib import Path

SOURCE=Path("E:/ORION/spikes/coding_mode_github_loop/reviewer_connector.py")
TARGETS={"open","mkdir","replace","rename","write_text","start","stop"}
class Visitor(ast.NodeVisitor):
 def __init__(self):self.stack=[];self.rows=[]
 def visit_ClassDef(self,n):
  self.stack.append("CLASS")
  self.generic_visit(n)
  self.stack.pop()
 def visit_FunctionDef(self,n):
  self.stack.append("FUNCTION")
  self.generic_visit(n)
  self.stack.pop()
 visit_AsyncFunctionDef=visit_FunctionDef
 def visit_Call(self,n):
  fn=n.func
  op=fn.attr if isinstance(fn,ast.Attribute) else fn.id if isinstance(fn,ast.Name) else ""
  if op in TARGETS:
   flags=[]
   if op=="open":
    args=list(n.args[1:])+[kw.value for kw in n.keywords if kw.arg=="mode"]
    for a in args:
     if isinstance(a,ast.Constant) and isinstance(a.value,str):
      if "x" in a.value:flags.append("EXCLUSIVE_CREATE")
      if "w" in a.value:flags.append("WRITE_MODE")
   if op=="mkdir":
    for kw in n.keywords:
     if kw.arg=="exist_ok" and isinstance(kw.value,ast.Constant):
      flags.append("EXIST_OK_TRUE" if kw.value.value is True else "EXIST_OK_FALSE")
   self.rows.append((n.lineno,op,",".join(flags) or "DEFAULT",self.stack[-1] if self.stack else "MODULE"))
  self.generic_visit(n)
def main():
 if not SOURCE.is_file():
  print("CONNECTOR_DETAIL> SOURCE_MISSING",flush=True)
  return
 try:tree=ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
 except (SyntaxError,UnicodeError,OSError) as exc:
  print("CONNECTOR_DETAIL> SOURCE_ERROR",type(exc).__name__,flush=True)
  return
 v=Visitor();v.visit(tree)
 for line,op,flags,context in sorted(v.rows):
  print("CONNECTOR_DETAIL> LINE",line,op,flags,context,flush=True)
 print("CONNECTOR_DETAIL> READ_ONLY_COMPLETE",len(v.rows),flush=True)
if __name__=="__main__":main()
