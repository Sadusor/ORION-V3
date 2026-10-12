import multiprocessing
import tempfile
import unittest
from pathlib import Path
from orion_v3.work_loop.durable_authorization_ledger_v1 import DurableAuthorizationLedger

N = "a"*32
H = "b"*64
R = "c"*40


def worker(path, output):
    output.put(DurableAuthorizationLedger(path).reserve(nonce=N, proposal_hash=H, source_revision=R))


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "auth.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def test_first_reservation(self):
        ledger = DurableAuthorizationLedger(self.path)
        self.assertTrue(ledger.reserve(nonce=N, proposal_hash=H, source_revision=R))
        self.assertTrue(ledger.contains(N))

    def test_replay_rejected(self):
        ledger = DurableAuthorizationLedger(self.path)
        self.assertTrue(ledger.reserve(nonce=N, proposal_hash=H, source_revision=R))
        self.assertFalse(ledger.reserve(nonce=N, proposal_hash=H, source_revision=R))

    def test_restart_persistence(self):
        DurableAuthorizationLedger(self.path).reserve(nonce=N, proposal_hash=H, source_revision=R)
        self.assertFalse(DurableAuthorizationLedger(self.path).reserve(nonce=N, proposal_hash=H, source_revision=R))

    def test_distinct_nonces(self):
        ledger = DurableAuthorizationLedger(self.path)
        self.assertTrue(ledger.reserve(nonce=N, proposal_hash=H, source_revision=R))
        self.assertTrue(ledger.reserve(nonce="d"*32, proposal_hash=H, source_revision=R))

    def test_invalid_nonce_rejected(self):
        ledger = DurableAuthorizationLedger(self.path)
        with self.assertRaises(ValueError):
            ledger.reserve(nonce="x' OR 1=1", proposal_hash=H, source_revision=R)

    def test_invalid_revision_rejected(self):
        ledger = DurableAuthorizationLedger(self.path)
        with self.assertRaises(ValueError):
            ledger.reserve(nonce=N, proposal_hash=H, source_revision="HEAD")

    def test_missing_parent_refused(self):
        with self.assertRaises(ValueError):
            DurableAuthorizationLedger(Path(self.temp.name)/"missing"/"auth.sqlite3")

    def test_two_processes_one_winner(self):
        DurableAuthorizationLedger(self.path)
        ctx = multiprocessing.get_context("spawn")
        queue = ctx.Queue()
        jobs = [ctx.Process(target=worker, args=(str(self.path), queue)) for _ in range(2)]
        for job in jobs: job.start()
        for job in jobs:
            job.join(20)
            self.assertEqual(job.exitcode, 0)
        self.assertEqual(sorted([queue.get(timeout=5) for _ in jobs]), [False, True])
        queue.close()
        queue.join_thread()


if __name__ == "__main__":
    unittest.main()
