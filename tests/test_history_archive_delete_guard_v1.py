"""Standalone Stage C guard tests; no production data or runtime."""
import tempfile
import unittest
from pathlib import Path

from src.orion_v3.modules.history_archive_delete_guard_v1 import (
    DeletedConversationReplay, OwnerDeleteLedgerV1
)


class DeleteGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "owner_delete_ledger.sqlite3"
        self.guard = OwnerDeleteLedgerV1(self.path)

    def payload(self, cid="c1", *, messages=True):
        return {"conversations": [{"id": cid, "project_id": "orion-v3"}],
                "messages": ([{"id": "m1", "conversation_id": cid}]
                             if messages else [])}

    def test_owner_authorization_required(self):
        with self.assertRaises(PermissionError):
            self.guard.record_owner_delete(
                conversation_id="c1", project_id="orion-v3",
                deleted_at_ms=12)
        self.guard.reject_replays(self.payload())

    def test_delete_blocks_stale_replay(self):
        self.guard.record_owner_delete(
            conversation_id="c1", project_id="orion-v3",
            deleted_at_ms=12, owner_authorized=True)
        with self.assertRaises(DeletedConversationReplay):
            self.guard.reject_replays(self.payload())

    def test_message_only_replay_blocked(self):
        self.guard.record_owner_delete(
            conversation_id="c1", project_id="orion-v3",
            deleted_at_ms=12, owner_authorized=True)
        with self.assertRaises(DeletedConversationReplay):
            self.guard.reject_replays({"conversations": [],
                                       "messages": [{"conversation_id": "c1"}]})

    def test_persists_across_restart(self):
        self.guard.record_owner_delete(
            conversation_id="c1", project_id="orion-v3",
            deleted_at_ms=12, owner_authorized=True)
        OwnerDeleteLedgerV1(self.path).reject_replays(self.payload("c2"))
        with self.assertRaises(DeletedConversationReplay):
            OwnerDeleteLedgerV1(self.path).reject_replays(self.payload())

    def test_project_collision_refused(self):
        self.guard.record_owner_delete(
            conversation_id="c1", project_id="orion-v3",
            deleted_at_ms=12, owner_authorized=True)
        with self.assertRaises(DeletedConversationReplay):
            self.guard.record_owner_delete(
                conversation_id="c1", project_id="other",
                deleted_at_ms=13, owner_authorized=True)

    def test_retry_idempotent_and_timestamp_monotonic(self):
        for ms in (12, 11, 20):
            self.guard.record_owner_delete(
                conversation_id="c1", project_id="orion-v3",
                deleted_at_ms=ms, owner_authorized=True)
        self.assertEqual(self.guard.tombstones()[0]["deleted_at_ms"], 20)

    def test_unrelated_conversation_accepted(self):
        self.guard.record_owner_delete(
            conversation_id="c1", project_id="orion-v3",
            deleted_at_ms=12, owner_authorized=True)
        self.guard.reject_replays(self.payload("c2"))

    def test_bad_payload_rejected(self):
        for p in (None, {"messages": "bad"}, {"conversations": [None]}):
            with self.assertRaises(ValueError):
                self.guard.reject_replays(p)


if __name__ == "__main__":
    unittest.main()
