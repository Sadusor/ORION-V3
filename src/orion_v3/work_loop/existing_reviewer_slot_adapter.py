"""One-model adapter for the existing ReviewerConnector.

The existing connector owns credentials and provider transport. ORION owns STOP,
attribution, bounded polling and proposal-only behavior. No patch execution.
"""
import time

class ReviewerInvocationError(Exception):
    def __init__(self, category):
        self.category=category
        super().__init__(category)

def invoke_existing(*, connector, reviewer_id, prompt, stop_requested, timeout=90,
                    poll_interval=0.25, clock=None, sleep=None):
    if not callable(stop_requested):
        raise ValueError("STOP callback required")
    if not isinstance(reviewer_id,str) or not reviewer_id.strip():
        raise ValueError("reviewer ID required")
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>12000:
        raise ValueError("bounded prompt required")
    if not 1<=timeout<=180 or not 0<poll_interval<=2:
        raise ValueError("invalid timing budget")
    clock=clock or time.monotonic
    sleep=sleep or time.sleep
    if stop_requested():
        raise ReviewerInvocationError("STOPPED")
    started=False
    try:
        connector.start(prompt,[reviewer_id],popup_windows=False)
        started=True
        deadline=clock()+timeout
        while clock()<deadline:
            if stop_requested():
                raise ReviewerInvocationError("STOPPED")
            state=connector.view()
            if not isinstance(state,dict):
                raise ReviewerInvocationError("MALFORMED_RESPONSE")
            entries=state.get("reviewers") or []
            if isinstance(entries,dict):
                entries=list(entries.values())
            if not isinstance(entries,list):
                raise ReviewerInvocationError("MALFORMED_RESPONSE")
            matching=[e for e in entries if isinstance(e,dict) and e.get("reviewer_id")==reviewer_id]
            if len(matching)>1:
                raise ReviewerInvocationError("MALFORMED_RESPONSE")
            if matching:
                entry=matching[0]
                status=str(entry.get("state") or "").lower()
                if status in {"failed","error","failure","denied","cancelled","canceled"}:
                    # Conservative: error strings may contain secrets; never propagate them.
                    raise ReviewerInvocationError("PROVIDER")
                if status in {"completed","complete","done"}:
                    output=entry.get("output")
                    if not isinstance(output,str) or not output.strip() or len(output)>16000:
                        raise ReviewerInvocationError("MALFORMED_RESPONSE")
                    return output
            if str(state.get("state") or "").lower() in {"completed","complete","done","error","failed","stopped"}:
                raise ReviewerInvocationError("MALFORMED_RESPONSE")
            sleep(poll_interval)
        raise ReviewerInvocationError("TRANSPORT")
    finally:
        if started:
            try:
                state=connector.view()
                if not isinstance(state,dict) or str(state.get("state") or "").lower() not in {
                    "completed","complete","done","error","failed","stopped"}:
                    connector.stop()
            except Exception:
                # Never replace the original failure; connector cleanup is best effort.
                pass
