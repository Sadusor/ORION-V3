"""Reproduce private reviewer connector state collisions without network or credentials.

A FileExistsError in connector.start is a structural collision, not a model
failure. Never delete connector state or retry with a different model blindly.
"""
from .existing_reviewer_slot_adapter import invoke_existing, ReviewerInvocationError

class ConnectorStateCollision(ReviewerInvocationError):
    def __init__(self):
        super().__init__("CONNECTOR_STATE_COLLISION")

def invoke_collision_safe(**kwargs):
    try:
        return invoke_existing(**kwargs)
    except FileExistsError:
        # Connector owns its workspace. We do not unlink or overwrite it.
        raise ConnectorStateCollision() from None
