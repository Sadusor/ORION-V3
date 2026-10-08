"""Integration qualification using ORION's real Vault code.

All tests use disposable temporary projects.
No production execution or canonical project modification.
"""
import multiprocessing as mp
import tempfile
import unittest
from pathlib import Path

from orion_v3.work_loop.contracts import WorkState, EvidenceRecord
from orion_v3.work_loop.vault import ProjectVault, VaultError
from orion_v3.work_loop.commit_coordinator import CommitCoordinator


def writer(root, start, queue):
    start.wait(8)
    try:
        vault = ProjectVault(root)
        vault.record_verified_result(
            EvidenceRecord(
                "test-project", "task-1", "a" * 64,
                "execution", "fail", "fixture", "rev1"
            ),
            next_action="blocked"
        )
        queue.put("OK")
    except Exception as exc:
        queue.put(type(exc).__name__ + ":" + str(exc))


class RealVaultQualification(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="orion-real-vault-")
        self.root = Path(self.tmp.name)
        self.vault = ProjectVault(self.root)
        self.vault.initialize(
            WorkState("test-project", "qualification", "initial", "task-1")
        )
        self.evidence = EvidenceRecord(
            "test-project", "task-1", "a" * 64,
            "execution", "fail", "fixture", "rev1"
        )

    def tearDown(self):
        self.tmp.cleanup()

    def snapshot(self):
        return (
            self.vault.state_path.read_bytes(),
            self.vault.journal_path.read_bytes()
        )

    def test_stop_guard_blocks_real_vault(self):
        before = self.snapshot()

        with self.assertRaises(VaultError):
            self.vault.record_verified_result(
                self.evidence,
                next_action="blocked",
                commit_guard=lambda: False
            )

        self.assertEqual(before, self.snapshot())
        print("REAL_VAULT_STOP_GUARD> PASS")

    def test_real_coordinator_stop_blocks_commit(self):
        coordinator = CommitCoordinator()
        generation = coordinator.snapshot()
        coordinator.stop()
        before = self.snapshot()

        with self.assertRaises(VaultError):
            self.vault.record_verified_result(
                self.evidence,
                next_action="blocked",
                commit_coordinator=coordinator,
                expected_generation=generation
            )

        self.assertEqual(before, self.snapshot())
        print("IN_PROCESS_STOP_COORDINATOR> PASS")

    def test_pending_recovery_idempotent(self):
        from orion_v3.work_loop.vault_transaction import new_pending

        state = self.vault.load()
        payload = {
            k: getattr(state, k)
            for k in state.__dataclass_fields__
        }
        payload["next_action"] = "recovered"

        pending = new_pending(
            "EXECUTION FAIL task=task-1",
            payload
        )

        self.vault._write_pending(pending)

        self.assertEqual(
            self.vault.load().next_action,
            "recovered"
        )

        first = self.vault.journal_path.read_text(encoding="utf-8")
        self.vault.load()

        self.assertEqual(
            first,
            self.vault.journal_path.read_text(encoding="utf-8")
        )
        self.assertEqual(
            first.count("txid=" + pending["txid"]),
            1
        )

        print("REAL_VAULT_RECOVERY_DEDUP> PASS")

    def test_cross_process_vault_serialization(self):
        ctx = mp.get_context("spawn")
        start = ctx.Event()
        queue = ctx.Queue()

        procs = [
            ctx.Process(
                target=writer,
                args=(str(self.root), start, queue)
            )
            for _ in range(3)
        ]

        try:
            for p in procs:
                p.start()

            start.set()

            results = [
                queue.get(timeout=20)
                for _ in procs
            ]

            for p in procs:
                p.join(10)

            self.assertTrue(
                all(p.exitcode == 0 for p in procs)
            )
            self.assertEqual(results, ["OK"] * 3)

            journal = self.vault.journal_path.read_text(
                encoding="utf-8"
            )

            self.assertEqual(journal.count("txid="), 3)
            self.assertFalse(self.vault.pending_path.exists())

            print("REAL_VAULT_MULTIPROCESS_SERIALIZATION> PASS")

        finally:
            for p in procs:
                if p.is_alive():
                    p.terminate()
                p.join(timeout=3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
