"""Read-only donor contract inspection; outputs bounded selected method source, never secrets.

Only inspect statically defined methods relevant to constructing and running the
existing reviewer connector. No imports, no execution, no credential loading.
"""
import ast
from pathlib import Path

root = Path("E:/ORION/spikes/coding_mode_github_loop")
targets = {
    "provider_vault.py": {"__init__", "list_entries", "view"},
    "reviewer_connector.py": {"__init__", "refresh_catalog", "catalog_view", "start",
                              "view", "stop", "_run_all", "_run_one"},
    "cloud_e2e_brainstorm_probe.py": {"main", "choose_reviewers"},
}
for name, methods in targets.items():
    path = root / name
    if not path.is_file():
        print("M4_DONOR_CONTRACT> MISSING", name)
        continue
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    print("M4_DONOR_CONTRACT> FILE", name)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name not in methods:
            continue
        # Only public control-flow source from explicitly selected methods.
        # Avoid emitting hard-coded strings, values, auth header construction,
        # local filesystem paths, and credentials: emit AST node shapes only.
        print("M4_DONOR_CONTRACT> METHOD", node.name, "line_count", node.end_lineno-node.lineno+1)
        for stmt in node.body[:24]:
            if isinstance(stmt, ast.Assign):
                print("M4_DONOR_CONTRACT> ASSIGN_TARGETS",
                      ",".join(ast.unparse(t) for t in stmt.targets)[:200])
            elif isinstance(stmt, ast.AnnAssign):
                print("M4_DONOR_CONTRACT> ANN_TARGET", ast.unparse(stmt.target)[:200])
            elif isinstance(stmt, ast.Return):
                print("M4_DONOR_CONTRACT> RETURN_SHAPE", type(stmt.value).__name__)
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                func = stmt.value.func
                if isinstance(func, ast.Attribute):
                    print("M4_DONOR_CONTRACT> CALL", func.attr)
            elif isinstance(stmt, (ast.If, ast.For, ast.Try, ast.With)):
                print("M4_DONOR_CONTRACT> CONTROL", type(stmt).__name__)
print("M4_DONOR_CONTRACT> AST_ONLY_NO_SECRETS_PASS")
