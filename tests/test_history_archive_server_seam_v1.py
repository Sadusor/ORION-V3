"""Guard the product-server wiring without booting or changing live ORION.

Also exercises the same underlying archive and replay operations on temp data.
"""
import tempfile
import unittest
from pathlib import Path

from src.orion_v3.modules.history_archive_v1 import HistoryArchiveV1
from src.orion_v3.modules.history_archive_delete_guard_v1 import (
    OwnerDeleteLedgerV1, DeletedConversationReplay,
)
from src.orion_v3.modules.history_archive_owner_capability_v1 import OwnerCapabilityV1
from src.orion_v3.modules.history_archive_sync_v1 import archive_first_sync
from src.orion_v3.modules.chat_history import ChatHistoryStore


SERVER = Path(__file__).resolve().parents[1] / "src" / "orion_v3" / "product_server.py"


class ServerSeamTests(unittest.TestCase):
    def test_server_gates_archiving_and_search(self):
        source = SERVER.read_text(encoding="utf-8")
        self.assertIn('ORION_HISTORY_ARCHIVE_V1_EXPERIMENTAL', source)
        self.assertIn('if path == "/api/history-archive/search":', source)
        self.assertIn('"archive disabled"', source)
        self.assertIn('"X-Orion-Archive-Owner"', source)
        self.assertIn('OwnerCapabilityV1(', source)

    def test_server_guard_runs_before_archive_first_sync(self):
        source = SERVER.read_text(encoding="utf-8")
        start = source.index('if path == "/api/chat-history/sync":')
        end = source.index('if path == "/api/memory/candidate":', start)
        section = source[start:end]
        self.assertLess(section.index('.reject_replays(body)'),
                        section.index('synced = archive_first_sync('))
        self.assertIn('synced = CHAT_HISTORY.sync(body)', section)

    def test_full_archive_search_and_stale_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = HistoryArchiveV1(root / "archive.sqlite3")
            live = ChatHistoryStore(root / "live.sqlite3")
            ledger = OwnerDeleteLedgerV1(root / "delete.sqlite3")
            payload = {"conversations": [{"id": "c1", "project_id": "orion-v3",
                       "created_at_ms": 10, "updated_at_ms": 20}],
                       "messages": [{"id": "m1", "conversation_id": "c1",
                       "role": "user", "text": "Archive test Ελληνικά " * 500,
                       "created_at_ms": 15}]}
            ledger.reject_replays(payload)
            archive_first_sync(payload, archive=archive, live_sync=live.sync)
            result = archive.query(project_id="orion-v3", contains="Ελληνικά")
            self.assertEqual(result[0]["text"], payload["messages"][0]["text"])
            ledger.record_owner_delete(conversation_id="c1",
                project_id="orion-v3", deleted_at_ms=50, owner_authorized=True)
            with self.assertRaises(DeletedConversationReplay):
                ledger.reject_replays(payload)

    def test_owner_proof_fails_closed_when_unenrolled(self):
        with tempfile.TemporaryDirectory() as temp:
            capability = OwnerCapabilityV1(Path(temp))
            self.assertFalse(capability.verify("paired-device"))
            self.assertFalse(capability.verify("x" * 60))


if __name__ == "__main__":
    unittest.main()
