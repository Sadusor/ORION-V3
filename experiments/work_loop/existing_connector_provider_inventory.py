"""Read-only provider connector inventory, excluding credentials and secret values.

Inspects the *existing* reviewer catalog and reports only provider counts and
model-family labels. No inference or credential lookup.
"""
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from live_two_cloud_architecture_demo import DONOR,runtime_from_existing_source

def main():
    sys.path.insert(0,str(DONOR))
    from provider_vault import ProviderVault
    from reviewer_connector import ReviewerConnector
    runtime=runtime_from_existing_source()
    connector=ReviewerConnector(runtime/"coding-mode"/"reviewers",
        provider_vault=ProviderVault(runtime/"provider-vault"),configured_free_providers=[])
    catalog=connector.refresh_catalog()
    models=catalog.get("models") or []
    counts=Counter()
    families=Counter()
    for m in models:
        if not isinstance(m,dict) or m.get("available") is not True:continue
        provider=str(m.get("provider") or "").lower()
        model=str(m.get("model") or "").lower()
        if provider in ("ollama","local") or not provider:continue
        counts[provider]+=1
        family=("gemini" if "gemini" in model else "gpt-oss" if "gpt-oss" in model
                else "qwen" if "qwen" in model else "llama" if "llama" in model
                else "other")
        families[(provider,family)]+=1
    for provider,n in sorted(counts.items()):
        print("ORION_CONNECTOR> PROVIDER",provider[:60],"AVAILABLE_MODELS",n,flush=True)
    for (provider,family),n in sorted(families.items()):
        print("ORION_CONNECTOR> FAMILY",provider[:60],family,"COUNT",n,flush=True)
    print("ORION_CONNECTOR> CATALOG_ONLY_NO_SECRETS_NO_INFERENCE",flush=True)

if __name__=="__main__":main()
