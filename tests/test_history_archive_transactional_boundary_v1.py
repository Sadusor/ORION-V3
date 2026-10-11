import tempfile
import unittest
from pathlib import Path
from src.orion_v3.modules.history_archive_write_gate_v1 import ArchiveWriteGateV1
from src.orion_v3.modules.history_archive_transactional_boundary_v1 import HistoryArchiveTransactionalBoundaryV1


class Ingress:
    def __init__(self): self.deleted = []
    def owner_delete(self, *, conversation_id, project_id, token):
        if token != "owner-only": raise PermissionError("owner required")
        self.deleted.append(conversation_id)
        return {"deleted": True}


class Sync:
    def __init__(self): self.calls = []
    def dispatch(self, *, device_token, body):
        if device_token != "project-scoped": return 403, {"ok": False}
        self.calls.append(body)
        return 200, {"ok": True}


class TransactionalBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.gate = ArchiveWriteGateV1(Path(self.tmp.name) / "gate.sqlite3")
        self.ingress, self.syncer = Ingress(), Sync()
        self.enabled = True
        self.boundary = HistoryArchiveTransactionalBoundaryV1(
            writer_gate=self.gate, reconciled_sync=self.syncer,
            ingress=self.ingress, enabled=lambda: self.enabled)

    def test_disabled_denies_both_routes(self):
        self.enabled = False
        self.assertEqual(self.boundary.sync(device_token="project-scoped", body={})[0], 404)
        self.assertEqual(self.boundary.owner_delete(
            owner_token="owner-only", conversation_id="c", project_id="p")[0], 404)
        self.assertFalse(self.syncer.calls)
        self.assertFalse(self.ingress.deleted)

    def test_sync_path(self):
        self.assertEqual(self.boundary.sync(
            device_token="project-scoped", body={"snapshot": {}})[0], 200)
        self.assertEqual(len(self.syncer.calls), 1)

    def test_pair_token_cannot_delete(self):
        self.assertEqual(self.boundary.owner_delete(
            owner_token="paired", conversation_id="c", project_id="p")[0], 403)
        self.assertFalse(self.ingress.deleted)

    def test_owner_delete(self):
        code, result = self.boundary.owner_delete(
            owner_token="owner-only", conversation_id="c", project_id="p")
        self.assertEqual(code, 200)
        self.assertEqual(result["deleted"], True)

    def test_lock_spans_entire_reconcile_and_sync(self):
        # Acquire same DB write lock externally. Both paths must fail closed
        # before entering delegates, proving the lock wraps their entry points.
        import sqlite3
        from contextlib import closing
        fast = ArchiveWriteGateV1(self.gate.path, timeout_seconds=.1)
        self.boundary.writer_gate = fast
        with closing(sqlite3.connect(str(self.gate.path), isolation_level=None)) as held:
            held.execute("BEGIN IMMEDIATE")
            with self.assertRaises(sqlite3.OperationalError):
                self.boundary.sync(device_token="project-scoped", body={})
            status, response = self.boundary.owner_delete(
                owner_token="owner-only", conversation_id="c", project_id="p")
            self.assertEqual(status, 409)
            self.assertFalse(response["ok"])
            held.execute("ROLLBACK")
        self.assertFalse(self.syncer.calls)
        self.assertFalse(self.ingress.deleted)


if __name__ == "__main__":
    unittest.main()
