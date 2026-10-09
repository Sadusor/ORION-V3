"""Live-readiness gate for ORION's existing Windows DPAPI vault.

Read-only metadata; never access secrets, create entries or send inference.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from live_two_cloud_architecture_demo import DONOR, runtime_from_existing_source

def main():
    sys.path.insert(0, str(DONOR))
    from provider_vault import ProviderVault
    vault = ProviderVault(runtime_from_existing_source() / "provider-vault")
    entries = vault.list_entries()
    if not isinstance(entries, list):
        raise RuntimeError("unexpected vault metadata type")
    # Only public metadata booleans; do not serialize records or credentials.
    for adapter in ("openrouter", "groq", "gemini"):
        matches = [row for row in entries if isinstance(row, dict)
                   and str(row.get("adapter") or "").lower() == adapter]
        ready = sum(1 for row in matches if row.get("enabled") is True
                    and row.get("has_secret") is True)
        print("ORION_PROVIDER_READY>", adapter.upper(), "ENTRIES", len(matches),
              "ENABLED_WITH_SECRET", ready, flush=True)
    print("ORION_PROVIDER_READY> NO_KEYS_NO_INFERENCE_NO_MUTATION", flush=True)

if __name__ == "__main__":
    main()
