"""Stage B optional archive-first chat-sync adapter.

Off by default at the product server. This does not replace ChatHistoryStore.
Do not mistake deleted=1 client metadata for a verified owner delete event.
"""
from __future__ import annotations

from typing import Any

from .history_archive_v1 import HistoryArchiveV1


class ArchiveSyncHold(RuntimeError):
    pass


def archive_first_sync(payload: dict[str, Any], *, archive: HistoryArchiveV1,
                       live_sync) -> dict[str, Any]:
    """Write raw messages to durable archive before bounded live-store sync.

    Deliberately fail closed on deletion flags until owner-delete semantics
    have been verified across PC and Android; do not lose archived messages.
    """
    if not isinstance(payload, dict):
        raise TypeError("Expected chat sync payload object")
    conversations = payload.get("conversations", [])
    messages = payload.get("messages", [])
    if not isinstance(conversations, list) or not isinstance(messages, list):
        raise TypeError("Invalid chat sync arrays")
    for row in conversations:
        if not isinstance(row, dict):
            raise TypeError("Invalid conversation row")
        if row.get("deleted"):
            raise ArchiveSyncHold(
                "Explicit deletion sync protocol not yet qualified; "
                "archive-enabled sync refused without mutating either store"
            )
    # Source data must carry an explicit project ID for an archive record.
    # The existing live store has legacy blank project IDs; fail closed
    # rather than silently weakening permanent archive scope.
    project_for = {
        str(row.get("id") or ""): str(row.get("project_id") or "").strip()
        for row in conversations
    }
    for row in messages:
        if not isinstance(row, dict):
            raise TypeError("Invalid message row")
        project = str(row.get("project_id") or "").strip() or project_for.get(
            str(row.get("conversation_id") or ""), ""
        )
        if not project:
            raise ArchiveSyncHold(
                "Archive-enabled sync requires explicit project provenance"
            )
    archive.append_batch(conversations, messages)
    return live_sync(payload)
