"""Bridge the existing ORION ReviewerConnector without duplicating API clients.

The caller injects an existing connector instance; this adapter never reads
credentials or chooses providers. Explicit reviewer IDs only. No execution.
"""
from __future__ import annotations
import time
from typing import Any

class ExistingReviewerBridge:
    def __init__(self, connector: Any):
        if not all(callable(getattr(connector, method, None))
                   for method in ("catalog_view", "start", "view", "stop")):
            raise ValueError("existing ReviewerConnector contract missing")
        self.connector = connector

    def catalog(self):
        return self.connector.catalog_view()

    def request(self, prompt: str, reviewer_ids: list[str], *,
                timeout_seconds: float = 90, stop_requested=None):
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 4096:
            raise ValueError("invalid bounded prompt")
        if (not isinstance(reviewer_ids, list) or not 1 <= len(reviewer_ids) <= 2
                or len(set(reviewer_ids)) != len(reviewer_ids)
                or any(not isinstance(x, str) or not x.strip() or len(x) > 100 for x in reviewer_ids)):
            raise ValueError("explicit distinct provider ids required")
        if not callable(stop_requested):
            raise ValueError("trusted STOP callback required")
        if stop_requested():
            raise RuntimeError("STOP before provider request")
        if not 1 <= timeout_seconds <= 120:
            raise ValueError("timeout out of bounds")
        self.connector.start(prompt, reviewer_ids, popup_windows=False)
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if stop_requested():
                self.connector.stop()
                raise RuntimeError("STOP during provider request")
            state = self.connector.view()
            if not isinstance(state, dict):
                raise RuntimeError("connector returned invalid state")
            if state.get("state") in ("complete", "completed", "done", "failed", "error", "stopped"):
                return state
            time.sleep(0.1)
        self.connector.stop()
        raise TimeoutError("provider request timed out")
