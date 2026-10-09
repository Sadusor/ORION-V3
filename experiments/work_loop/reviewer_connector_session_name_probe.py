"""Read-only AST analysis of session naming and directory reuse.

Prints structural types and presence of time/random/UUID generation only;
never prints identifiers, literals, paths, provider data or source lines.
"""
import ast
from pathlib import Path
SOURCE=Path("E:/ORION/spikes/coding_mode_github_loop/reviewer_connector.py")
def category(n):
 if isinstance(n,ast.Call):
  f=n.func
  name=f.attr if isinstance(f,ast.Attribute) else f.id if isinstance(f,ast.Name) else ""
  if name in ("uuid4","uuid1","token_hex","token_urlsafe","urandom"):return "RANDOM_OR_UUID_CALL"
  if name in ("time","time_ns","now","utcnow","strftime","isoformat"):return "TIME_CALL"
  if name in ("getpid","get_ident"):return "PROCESS_OR_THREAD_CALL"
  return "OTHER_CALL"
 if isinstance(n,ast.Name):return "VARIABLE"
 if isinstance(n,ast.Attribute):return "ATTRIBUTE"
 if isinstance(n,ast.Constant):return "CONSTANT_"+type(n.value).__name__.upper()
 return type(n).__name__.upper()
def main():
 if not SOURCE.is_file():
  print("CONNECTOR_NAME> SOURCE_MISSING",flush=True);return
 tree=ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
 fns=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.lineno==527]
 if len(fns)!=1:
  print("CONNECTOR_NAME> FUNCTION_SHAPE_CHANGED",flush=True);return
 fn=fns[0]
 for stmt in ast.walk(fn):
  if isinstance(stmt,(ast.Assign,ast.AnnAssign)) and stmt.lineno in (557,558,559,560):
   val=stmt.value
   if isinstance(val,ast.JoinedStr):
    segments=[category(v.value) for v in val.values if isinstance(v,ast.FormattedValue)]
    print("CONNECTOR_NAME> LINE",stmt.lineno,"FSTRING_COMPONENTS",",".join(segments),flush=True)
   else:
    calls=[category(n) for n in ast.walk(val) if isinstance(n,ast.Call)]
    print("CONNECTOR_NAME> LINE",stmt.lineno,"CALL_CATEGORIES",",".join(calls) or "NONE",flush=True)
 print("CONNECTOR_NAME> READ_ONLY_COMPLETE",flush=True)
if __name__=="__main__":main()
