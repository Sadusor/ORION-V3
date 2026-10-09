"""Inspect vault method contracts statically, without importing or opening secrets."""
import ast
from pathlib import Path
DONOR = Path("E:/ORION/spikes/coding_mode_github_loop")
NAMES = {"get", "get_secret", "upsert", "list_entries", "view"}
def main():
    path = DONOR / "provider_vault.py"
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ProviderVault":
            for fn in node.body:
                if isinstance(fn, ast.FunctionDef) and fn.name in NAMES:
                    args = [x.arg for x in fn.args.args]
                    defaults = [ast.unparse(x)[:100] for x in fn.args.defaults]
                    annotations = ast.unparse(fn.returns)[:100] if fn.returns else "none"
                    calls = sorted({ast.unparse(n.func)[:75] for n in ast.walk(fn)
                                    if isinstance(n, ast.Call) and isinstance(n.func, (ast.Name, ast.Attribute))
                                    and not any(w in ast.unparse(n.func).lower() for w in ("decrypt", "protect", "unprotect"))})
                    print("ORION_VAULT_CONTRACT> METHOD", fn.name, "ARGS", ",".join(args),
                          "DEFAULTS", ",".join(defaults), "RET", annotations,
                          "CALLS", ",".join(calls[:18]), flush=True)
    print("ORION_VAULT_CONTRACT> AST_ONLY_NO_SECRET_READ", flush=True)
if __name__ == "__main__": main()
