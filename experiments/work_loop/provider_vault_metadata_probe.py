"""Safe vault metadata inventory. Never fetch or print secret values."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from live_two_cloud_architecture_demo import DONOR, runtime_from_existing_source

def main():
    sys.path.insert(0, str(DONOR))
    from provider_vault import ProviderVault
    vault = ProviderVault(runtime_from_existing_source() / "provider-vault")
    # Prefer metadata-only view; never call get_secret or serialize entry records.
    view = vault.view()
    if isinstance(view, dict):
        print("ORION_VAULT_META> VIEW_TOP_LEVEL_KEYS", ",".join(sorted(str(k) for k in view)), flush=True)
    else:
        print("ORION_VAULT_META> VIEW_TYPE", type(view).__name__, flush=True)
    print("ORION_VAULT_META> NO_SECRET_ACCESS", flush=True)

if __name__ == "__main__":
    main()
