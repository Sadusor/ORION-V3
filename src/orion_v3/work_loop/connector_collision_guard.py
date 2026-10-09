"""Fail-closed containment and sanitized provenance for donor FileExistsError.

Never logs paths, source lines, exception messages or provider payloads.
"""
from .existing_reviewer_slot_adapter import invoke_existing, ReviewerInvocationError

def sanitized_origin(exc):
    """Report the relevant donor frame, not a generic stdlib traceback leaf."""
    frames = []
    tb = exc.__traceback__
    while tb is not None:
        filename = tb.tb_frame.f_code.co_filename.replace("\\\\", "/")
        if filename.endswith("/reviewer_connector.py"):
            frames.append(("DONOR_REVIEWER_CONNECTOR", tb.tb_lineno))
        elif filename.endswith("/existing_reviewer_slot_adapter.py"):
            frames.append(("ORION_SLOT_ADAPTER", tb.tb_lineno))
        elif filename.endswith("/pathlib.py") or "/pathlib/" in filename:
            frames.append(("PYTHON_PATHLIB", tb.tb_lineno))
        else:
            frames.append(("OTHER_MODULE", tb.tb_lineno))
        tb = tb.tb_next
    for origin, line in reversed(frames):
        if origin == "DONOR_REVIEWER_CONNECTOR":
            return origin, line
    for origin, line in reversed(frames):
        if origin == "ORION_SLOT_ADAPTER":
            return origin, line
    return frames[-1] if frames else ("UNKNOWN", 0)

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
