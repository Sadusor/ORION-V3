"""Offline bridge contract and STOP tests; no provider calls."""
from orion_v3.work_loop.existing_reviewer_bridge import ExistingReviewerBridge

class Fake:
    def __init__(self): self.stopped = False; self.started = []
    def catalog_view(self): return {"providers": ["existing"]}
    def start(self, prompt, reviewer_ids, popup_windows=False):
        self.started.append((prompt, reviewer_ids, popup_windows))
    def view(self): return {"state": "completed", "results": []}
    def stop(self): self.stopped = True

f = Fake()
bridge = ExistingReviewerBridge(f)
assert bridge.catalog()["providers"] == ["existing"]
result = bridge.request("bounded review", ["existing"], stop_requested=lambda: False)
assert result["state"] == "completed"
assert f.started == [("bounded review", ["existing"], False)]
print("M4_EXISTING_API> REUSED_REVIEWER_CONNECTOR_CONTRACT_PASS")
for ids in ([], ["duplicate", "duplicate"], ["a", "b", "c"]):
    try: bridge.request("task", ids, stop_requested=lambda: False)
    except ValueError: pass
    else: raise AssertionError("invalid provider list accepted")
print("M4_EXISTING_API> PROVIDER_SELECTION_DENIAL_PASS")
try: bridge.request("task", ["existing"], stop_requested=lambda: True)
except RuntimeError: pass
else: raise AssertionError("STOP bypassed")
assert len(f.started) == 1
print("M4_EXISTING_API> PRE_REQUEST_STOP_PASS")
print("M4_EXISTING_API> REAL_API_CALL_NOT_YET_QUALIFIED")
