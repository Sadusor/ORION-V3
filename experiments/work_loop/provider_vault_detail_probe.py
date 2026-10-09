"""Read-only vault provider presence and API signatures; no credential values."""
import ast
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from live_two_cloud_architecture_demo import DONOR, runtime_from_existing_source

def main():
    source = DONOR / "provider_vault.py"
    tree = ast.parse(source.read_text(encoding="utf-8-sig"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ProviderVault":
            for method in node.body:
                if isinstance(method, ast.FunctionDef) and method.name in {"get", "get_secret", "list_entries", "view"}:
                    args = [a.arg for a in method.args.args]
                    print("ORION_VAULT_DETAIL> SIGNATURE", method.name, ",".join(args), flush=True)
    sys.path.insert(0, str(DONOR))
    from provider_vault import ProviderVault
    vault = ProviderVault(runtime_from_existing_source() / "provider-vault")
    metadata = vault.view()
    providers = metadata.get("providers") if isinstance(metadata, dict) else None
    if isinstance(providers, dict):
        labels = sorted(str(k).lower() for k in providers.keys())
    elif isinstance(providers, list):
        labels = sorted(str(x.get("provider") or x.get("adapter") or x.get("name") or "unknown").lower()
                        for x in providers if isinstance(x, dict))
    else:
        labels = []
    # Only print normalized provider names; never serialize provider records.
    print("ORION_VAULT_DETAIL> PROVIDER_LABELS", ",".join(labels) or "none", flush=True)
    print("ORION_VAULT_DETAIL> OPENROUTER_LISTED", "yes" if "openrouter" in labels else "no", flush=True)
    print("ORION_VAULT_DETAIL> NO_SECRET_ACCESS_NO_INFERENCE", flush=True)

if __name__ == "__main__":
    main()
