"""Inspect original cloud probe wiring as AST only, without secrets or API calls."""
import ast
from pathlib import Path
p=Path("E:/ORION/spikes/coding_mode_github_loop/cloud_e2e_brainstorm_probe.py")
tree=ast.parse(p.read_text(encoding="utf-8-sig"))
for node in ast.walk(tree):
    if isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id in {"runtime","vault","review_root","connector","catalog","models","chosen","reviewer_ids"} for t in node.targets):
        names=",".join(t.id for t in node.targets if isinstance(t,ast.Name))
        expr=ast.unparse(node.value)
        # These expressions are repository source only; redact all literal string contents.
        scrubbed=ast.parse(expr,mode="eval")
        class Redact(ast.NodeTransformer):
            def visit_Constant(self,n):
                if isinstance(n.value,str): return ast.copy_location(ast.Constant(value="<literal>"),n)
                return n
        expr=ast.unparse(Redact().visit(scrubbed))
        print("M4_LIVE_WIRING> ASSIGN",names,expr[:450])
    if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in {"ProviderVault","ReviewerConnector"}:
        print("M4_LIVE_WIRING> CONSTRUCT",node.func.id,
              "args",",".join(ast.unparse(x)[:80] for x in node.args),
              "kwargs",",".join(x.arg or "unpacked" for x in node.keywords))
print("M4_LIVE_WIRING> AST_ONLY_NO_API_CALL_PASS")
