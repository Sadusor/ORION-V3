"""Safe structural inventory of existing ORION cloud provider implementation.

Reads source code locally, but prints only imports, function/class signatures and
non-sensitive module references. Never prints source bodies, defaults, environment,
configuration values, tokens or network responses.
"""
from __future__ import annotations
import ast
from pathlib import Path

root = Path("E:/ORION/spikes/coding_mode_github_loop")
names = ["provider_vault.py", "reviewer_connector.py", "cloud_e2e_brainstorm_probe.py",
         "orion_agent_v0_cloud_council_probe.py"]
for name in names:
    path = root / name
    if not path.is_file():
        print("M4_PROVIDER_INSPECT> MISSING", name)
        continue
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    except (UnicodeError, SyntaxError, OSError) as exc:
        print("M4_PROVIDER_INSPECT> UNREADABLE", name, type(exc).__name__)
        continue
    print("M4_PROVIDER_INSPECT> MODULE", name)
    for node in tree.body:
        if isinstance(node, ast.Import):
            print("M4_PROVIDER_INSPECT> IMPORT", ",".join(alias.name for alias in node.names)[:240])
        elif isinstance(node, ast.ImportFrom):
            print("M4_PROVIDER_INSPECT> FROM", str(node.module or "")[:120],
                  ",".join(alias.name for alias in node.names)[:240])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs]
            print("M4_PROVIDER_INSPECT> FUNCTION", node.name, ",".join(args)[:240])
        elif isinstance(node, ast.ClassDef):
            print("M4_PROVIDER_INSPECT> CLASS", node.name)
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg for a in sub.args.posonlyargs + sub.args.args + sub.args.kwonlyargs]
                    print("M4_PROVIDER_INSPECT> METHOD", node.name+"."+sub.name, ",".join(args)[:240])
print("M4_PROVIDER_INSPECT> STRUCTURAL_ONLY_NO_SECRETS_PASS")
