"""Collision-resistant IDs for future ORION-owned connector sessions.

Does not modify donor state or relax fail-closed directory creation.
"""
from datetime import datetime, timezone
from secrets import token_hex

def new_session_id(now=None, entropy=None):
    """UTC microseconds + 128 random bits, with injectable inputs for tests."""
    instant = now if now is not None else datetime.now(timezone.utc)
    if instant.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    instant = instant.astimezone(timezone.utc)
    suffix = entropy if entropy is not None else token_hex(16)
    if len(suffix) != 32 or any(c not in "0123456789abcdef" for c in suffix):
        raise ValueError("entropy must be 32 lowercase hex characters")
    return instant.strftime("%Y%m%dT%H%M%S%fZ") + "-" + suffix
