"""Read-only provider wiring discovery. Never fetches credentials or sends requests."""
import ast
from pathlib import Path
root = Path("E:/ORION/spikes/coding_mode_github_loop")
for name in ("cloud_e2e_brainstorm_probe.py", "reviewer_connector.py"):
    tree = ast.parse((root/name).read_text(encoding="utf-8-sig"))
    print("M4_WIRING> FILE", name)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in ("ProviderVault", "ReviewerConnector"):
                print("M4_WIRING> CONSTRUCTOR", func.id,
                      "POSITIONAL_TYPES", ",".join(type(a).__name__ for a in node.args),
                      "KEYWORDS", ",".join(k.arg or "unpacked" for k in node.keywords))
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("runtime", "review_root", "vault", "connector"):
                    value = node.value
                    if isinstance(value, ast.Call):
                        fn = value.func
                        print("M4_WIRING> ASSIGN", target.id, "CALL",
                              fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else "other")
        if isinstance(node, ast.FunctionDef) and node.name in ("catalog_view", "view", "start"):
            if name == "reviewer_connector.py":
                print("M4_WIRING> METHOD", node.name, "RETURN_FIELDS",
                      ",".join(sorted({k.value for x in ast.walk(node) if isinstance(x, ast.Dict)
                                      for k in x.keys if isinstance(k, ast.Constant) and isinstance(k.value,str)}))[:300])
print("M4_WIRING> READ_ONLY_PASS")
