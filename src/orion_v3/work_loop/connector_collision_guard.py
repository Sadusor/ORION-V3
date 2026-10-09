"""Fail-closed containment and sanitized provenance for donor FileExistsError.

Never logs paths, source lines, exception messages or provider payloads.
"""
from .existing_reviewer_slot_adapter import invoke_existing, ReviewerInvocationError

def sanitized_origin(exc):
    tb = exc.__traceback__
    last = None
    while tb is not None:
        last = tb
        tb = tb.tb_next
    if last is None:
        return "UNKNOWN", 0
    filename = last.tb_frame.f_code.co_filename.replace("\\", "/")
    if filename.endswith("/reviewer_connector.py"):
        source = "DONOR_REVIEWER_CONNECTOR"
    elif filename.endswith("/existing_reviewer_slot_adapter.py"):
        source = "ORION_SLOT_ADAPTER"
    else:
        source = "OTHER_MODULE"
    return source, last.tb_lineno

class ConnectorStateCollision(ReviewerInvocationError):
    def __init__(self, origin="UNKNOWN", line=0):
        super().__init__("CONNECTOR_STATE_COLLISION")
        self.origin = origin
        self.line = line

def invoke_collision_safe(**kwargs):
    try:
        return invoke_existing(**kwargs)
    except FileExistsError as exc:
        origin, line = sanitized_origin(exc)
        # No retry, deletion, mutation, or raw traceback exposure.
        raise ConnectorStateCollision(origin, line) from None
