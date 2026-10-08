"""Static smoke check of cloud trial launcher; never contacts cloud or runs generated code."""
import ast
from pathlib import Path
p=Path(__file__).with_name("task_ledger_cloud_trial_001.py")
tree=ast.parse(p.read_text(encoding="utf-8"))
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main")
defined={t.id for n in ast.walk(main) if isinstance(n,(ast.Assign,ast.AnnAssign)) for t in (n.targets if isinstance(n,ast.Assign) else [n.target]) if isinstance(t,ast.Name)}
assert "contract" in defined and "prompt" in defined
assert not any(isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load) and n.id=="task" for n in ast.walk(main)), "undefined task variable"
print("LEDGER_CLOUD_PREFLIGHT> PROMPT_VARIABLES_PASS")
print("LEDGER_CLOUD_PREFLIGHT> NO_PROVIDER_CALLED")
