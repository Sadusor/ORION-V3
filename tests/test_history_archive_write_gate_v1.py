"""Single-batch disabled archive write gate qualification."""
import sqlite3
import tempfile
import threading
import time
import unittest
from pathlib import Path

from src.orion_v3.modules.history_archive_write_gate_v1 import (
    ArchiveWriteGateV1, SerializedHistoryOperationsV1,
)


class RecorderIngress:
    def __init__(self):
        self.calls = []

    def sync(self, *, payload, token, local_trusted):
        if token != "authorized" or local_trusted:
            raise PermissionError("sync denied")
        self.calls.append(("sync", payload))
        return {"ok": True}

    def owner_delete(self, *, conversation_id, project_id, token):
        if token != "owner":
            raise PermissionError("delete denied")
        self.calls.append(("delete", conversation_id, project_id))
        return {"deleted": True}


class WriterGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dbpath = Path(self.temp.name) / "write-gate.sqlite3"
        self.gate = ArchiveWriteGateV1(self.dbpath, timeout_seconds=1)

    def test_serial_sync(self):
        record = RecorderIngress()
        ops = SerializedHistoryOperationsV1(gate=self.gate, ingress=record)
        self.assertTrue(ops.sync(payload={"messages": []}, token="authorized")["ok"])
        self.assertEqual(record.calls[0][0], "sync")

    def test_delete_owner_checked_by_ingress(self):
        record = RecorderIngress()
        ops = SerializedHistoryOperationsV1(gate=self.gate, ingress=record)
        with self.assertRaises(PermissionError):
            ops.owner_delete(conversation_id="c1", project_id="p", token="paired")
        self.assertEqual(record.calls, [])
        self.assertTrue(ops.owner_delete(
            conversation_id="c1", project_id="p", token="owner")["deleted"])

    def test_rollback_after_failure(self):
        with self.assertRaises(RuntimeError):
            self.gate.run_exclusive(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        self.assertEqual(self.gate.run_exclusive(lambda: "recovered"), "recovered")

    def test_two_gate_instances_serialize(self):
        other = ArchiveWriteGateV1(self.dbpath, timeout_seconds=1)
        entered = threading.Event()
        release = threading.Event()
        ordering = []
        errors = []
        def first():
            try:
                self.gate.run_exclusive(lambda: (
                    ordering.append("first-begin"),
                    entered.set(), release.wait(1), ordering.append("first-end")))
            except Exception as exc:
                errors.append(exc)
        def second():
            try:
                other.run_exclusive(lambda: ordering.append("second"))
            except Exception as exc:
                errors.append(exc)
        a = threading.Thread(target=first)
        b = threading.Thread(target=second)
        a.start()
        self.assertTrue(entered.wait(1))
        b.start()
        time.sleep(.05)
        self.assertEqual(ordering, ["first-begin"])
        release.set()
        a.join(2)
        b.join(2)
        self.assertFalse(errors)
        self.assertEqual(ordering, ["first-begin", "first-end", "second"])

    def test_second_writer_lock_timeout_fails_closed(self):
        second = ArchiveWriteGateV1(self.dbpath, timeout_seconds=.1)
        with sqlite3.connect(str(self.dbpath), isolation_level=None) as held:
            held.execute("BEGIN IMMEDIATE")
            with self.assertRaises(sqlite3.OperationalError):
                second.run_exclusive(lambda: "not allowed")
            held.execute("ROLLBACK")


if __name__ == "__main__":
    unittest.main()
