"""Offline client reconciliation contract, isolated and NOT wired to clients.

Server tombstones take precedence over offline stale snapshots. Produces
filtered safe deltas without authorizing deletion or modifying local stores.
"""
from __future__ import annotations


class ReconciliationError(ValueError):
    pass


def reconcile_client_snapshot(snapshot: dict, tombstones: list[dict]) -> dict:
    if not isinstance(snapshot, dict) or not isinstance(tombstones, list):
        raise ReconciliationError("Invalid reconciliation input")
    conversations = snapshot.get("conversations", [])
    messages = snapshot.get("messages", [])
    if not isinstance(conversations, list) or not isinstance(messages, list):
        raise ReconciliationError("Invalid snapshot arrays")
    deleted = {}
    for row in tombstones:
        if not isinstance(row, dict):
            raise ReconciliationError("Invalid tombstone")
        cid = row.get("conversation_id")
        project = row.get("project_id")
        if not isinstance(cid, str) or not cid or not isinstance(project, str) or not project:
            raise ReconciliationError("Unscoped tombstone")
        if cid in deleted and deleted[cid] != project:
            raise ReconciliationError("Conflicting tombstone scope")
        deleted[cid] = project
    retained_conversations = []
    local_projects = {}
    for row in conversations:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise ReconciliationError("Invalid conversation")
        cid = row["id"]
        project = row.get("project_id", "")
        if cid in deleted:
            if project and project != deleted[cid]:
                raise ReconciliationError("Conversation ID crossed project scopes")
            continue
        local_projects[cid] = project
        retained_conversations.append(row)
    retained_messages = []
    for row in messages:
        if not isinstance(row, dict) or not isinstance(row.get("conversation_id"), str):
            raise ReconciliationError("Invalid message")
        if row["conversation_id"] not in deleted:
            retained_messages.append(row)
    return {"schema": snapshot.get("schema", "orion.chat-history/1"),
            "conversations": retained_conversations,
            "messages": retained_messages,
            "removed_conversation_ids": sorted(deleted)}
