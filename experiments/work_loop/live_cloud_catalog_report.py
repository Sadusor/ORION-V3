"""Read-only catalog discovery through existing configured provider connector."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from live_two_cloud_architecture_demo import DONOR, runtime_from_existing_source
from cloud_catalog_report import report

def main():
    sys.path.insert(0, str(DONOR))
    from provider_vault import ProviderVault
    from reviewer_connector import ReviewerConnector
    runtime = runtime_from_existing_source()
    connector = ReviewerConnector(runtime / "coding-mode" / "reviewers",
                                  provider_vault=ProviderVault(runtime / "provider-vault"),
                                  configured_free_providers=[])
    print("ORION_CATALOG> READ_ONLY_START", flush=True)
    print("ORION_CATALOG> " + report(connector.refresh_catalog()), flush=True)
    print("ORION_CATALOG> END_NO_INFERENCE_NO_EXECUTION", flush=True)

if __name__ == "__main__":
    main()
