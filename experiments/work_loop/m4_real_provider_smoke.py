"""Real cloud-provider smoke test via ORIGINAL ORION connector and vault.

No credential reads or output, no file/code execution by a model. This test
requires an explicit owner-initiated remote run; only one small cloud prompt.
"""
from __future__ import annotations
import importlib.util
import os
import sys
import time
from pathlib import Path

donor=Path("E:/ORION/spikes/coding_mode_github_loop")
if not (donor/"provider_vault.py").is_file() or not (donor/"reviewer_connector.py").is_file():
    raise RuntimeError("original ORION provider modules unavailable")
sys.path.insert(0,str(donor))
from provider_vault import ProviderVault
from reviewer_connector import ReviewerConnector

runtime=Path(os.environ.get("ORION_RUNTIME_DIR",str(Path.home())))/".orion"/"runtime"
vault=ProviderVault(runtime/"provider-vault")
review_root=runtime/"coding-mode"/"reviewers"
connector=ReviewerConnector(review_root,provider_vault=vault,configured_free_providers=[])
catalog=connector.refresh_catalog()
models=list(catalog.get("models") or [])
cloud=[m for m in models if isinstance(m,dict)
       and str(m.get("provider") or m.get("adapter") or "").lower() not in ("ollama","local")
       and m.get("id")]
print("M4_LIVE_PROVIDER> CATALOG_MODELS",len(models),"CLOUD_CANDIDATES",len(cloud))
if not cloud:
    print("M4_LIVE_PROVIDER> NO_CONFIGURED_CLOUD_CANDIDATE")
    raise SystemExit(0)
selected=str(cloud[0]["id"])
print("M4_LIVE_PROVIDER> SELECTED_EXISTING_PROVIDER",str(cloud[0].get("provider") or cloud[0].get("adapter") or "configured")[:50])
prompt="ORION V3 connectivity check. Reply exactly: ORION_PROVIDER_READY. Do not execute code or request tools."
connector.start(prompt,[selected],popup_windows=False)
deadline=time.monotonic()+60
try:
    while time.monotonic()<deadline:
        state=connector.view()
        reviewers=state.get("reviewers") or []
        if isinstance(reviewers,dict):
            reviewers=list(reviewers.values())
        if any(isinstance(x,dict) and str(x.get("state") or "").lower() in ("completed","complete","failed","error") for x in reviewers):
            break
        if str(state.get("state") or "").lower() in ("completed","complete","failed","error","stopped"):
            break
        time.sleep(.25)
    else:
        print("M4_LIVE_PROVIDER> TIMEOUT")
        connector.stop()
        raise SystemExit(2)
    state=connector.view()
    reviewers=state.get("reviewers") or []
    if isinstance(reviewers,dict): reviewers=list(reviewers.values())
    states=[str(x.get("state") or "") for x in reviewers if isinstance(x,dict)]
    print("M4_LIVE_PROVIDER> REVIEWER_STATES",",".join(states)[:150])
    print("M4_LIVE_PROVIDER> MANIFEST_STATE",str(state.get("state") or "")[:60])
    # Do not print response text, provider IDs, usage details, paths, or secrets.
    print("M4_LIVE_PROVIDER> REQUEST_FINISHED_REVIEW_OUTPUT_NOT_YET_VALIDATED")
finally:
    connector.stop()
