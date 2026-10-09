"""Credential presence only: inspect ORION vault API surface without reading secrets.

Never emit environment variable values, vault records or keys.
"""
import ast
from pathlib import Path

DONOR = Path("E:/ORION/spikes/coding_mode_github_loop")
def main():
    path = DONOR / "provider_vault.py"
    if not path.is_file():
        raise RuntimeError("existing provider vault missing")
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ProviderVault":
            methods = sorted(n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                             and not n.name.startswith("_"))
            print("ORION_VAULT_API> PUBLIC_METHOD_NAMES", ",".join(methods), flush=True)
    print("ORION_VAULT_API> SOURCE_AST_ONLY_NO_SECRETS", flush=True)

if __name__ == "__main__":
    main()
