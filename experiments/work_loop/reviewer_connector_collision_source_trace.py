"""Read-only local inspection of donor connector state-file creation.

Prints only source line numbers, AST node types, and safe operation labels.
Never prints paths, source text, provider payloads, or credentials.
"""
import ast
from pathlib import Path

DONOR = Path("E:/ORION/spikes/coding_mode_github_loop")
FILES = ("reviewer_connector.py", "cloud_e2e_brainstorm_probe.py")
CALLS = {"open", "mkdir", "makedirs", "touch", "write_text", "write_bytes",
         "replace", "rename", "start", "stop", "unlink", "rmtree"}
def inspect_file(path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    rows=[]
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn=node.func
            name=fn.attr if isinstance(fn, ast.Attribute) else fn.id if isinstance(fn, ast.Name) else ""
            if name in CALLS:
                rows.append((node.lineno,name))
        elif isinstance(node, ast.With):
            rows.append((node.lineno,"WITH_CONTEXT"))
        elif isinstance(node, ast.ExceptHandler) and node.type is not None:
            if isinstance(node.type,ast.Name) and node.type.id=="FileExistsError":
                rows.append((node.lineno,"HANDLES_FILE_EXISTS"))
    return sorted(set(rows))
def main():
    for filename in FILES:
        path=DONOR/filename
        if not path.is_file():
            print("CONNECTOR_TRACE> SOURCE_MISSING",filename,flush=True)
            continue
        try:
            rows=inspect_file(path)
        except (SyntaxError,UnicodeError,OSError) as exc:
            print("CONNECTOR_TRACE> SOURCE_UNREADABLE",filename,type(exc).__name__,flush=True)
            continue
        print("CONNECTOR_TRACE> FILE",filename,"OPERATIONS",len(rows),flush=True)
        for lineno,label in rows[:120]:
            print("CONNECTOR_TRACE> LINE",lineno,label,flush=True)
    print("CONNECTOR_TRACE> READ_ONLY_NO_CREDENTIALS_NO_MUTATION",flush=True)
if __name__=="__main__":
    main()
