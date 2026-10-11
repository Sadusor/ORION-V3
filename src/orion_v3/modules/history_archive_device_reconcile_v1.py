"""Stage C read-only offline-client delete reconciliation bridge.

Not connected to HTTP, Android or live startup. Export only one project's
tombstones and remove stale local snapshot rows before any client re-upload.
No authorization or deletion is granted by this helper.
"""
from __future__ import annotations

from .history_archive_client_reconcile_v1 import (
    ReconciliationError, reconcile_client_snapshot,
)


def reconcile_project_snapshot(*, project_id: str, snapshot: dict, ledger) -> dict:
    if not isinstance(project_id, str) or not project_id.strip() or len(project_id) > 160:
        raise ReconciliationError("Valid project required")
    if not isinstance(snapshot, dict):
        raise ReconciliationError("Invalid snapshot")
    conversations = snapshot.get("conversations", [])
    messages = snapshot.get("messages", [])
    if not isinstance(conversations, list) or not isinstance(messages, list):
        raise ReconciliationError("Invalid snapshot arrays")
    if len(conversations) > 10000 or len(messages) > 100000:
        raise ReconciliationError("Snapshot exceeds reconciliation budget")

    # Reject cross-project uploads even when their IDs are not tombstoned.
    known = {}
    for row in conversations:
        if not isinstance(row, dict):
            raise ReconciliationError("Invalid conversation row")
        cid, scope = row.get("id"), row.get("project_id")
        if not isinstance(cid, str) or not cid:
            raise ReconciliationError("Missing conversation identity")
        if scope != project_id or (cid in known and known[cid] != scope):
            raise ReconciliationError("Conversation outside requested project")
        known[cid] = scope
    for row in messages:
        if not isinstance(row, dict) or not isinstance(row.get("conversation_id"), str):
            raise ReconciliationError("Invalid message row")
        if row["conversation_id"] not in known:
            raise ReconciliationError("Orphan or foreign-project message")

    tombstones = ledger.tombstones()
    if not isinstance(tombstones, list):
        raise ReconciliationError("Invalid tombstone ledger")
    selected = []
    for row in tombstones:
        if not isinstance(row, dict):
            raise ReconciliationError("Invalid tombstone row")
        cid, scope = row.get("conversation_id"), row.get("project_id")
        if not isinstance(cid, str) or not cid or not isinstance(scope, str) or not scope:
            raise ReconciliationError("Invalid tombstone identity")
        if scope == project_id:
            selected.append(row)
        elif cid in known:
            raise ReconciliationError("Conversation identity conflicts with other project")
    result = reconcile_client_snapshot(snapshot, selected)
    # Return only deleted IDs actually present in this client's project snapshot;
    # never leak identities of unrelated deleted conversations to a device.
    result["removed_conversation_ids"] = sorted(
        set(result["removed_conversation_ids"]) & set(known)
    )
    return result
