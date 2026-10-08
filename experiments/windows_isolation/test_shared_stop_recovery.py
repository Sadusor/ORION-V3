"""Real Vault crash-recovery and commit-first STOP qualification (disposable)."""
import tempfile
import unittest
from shared_stop_prototype import SharedStop
from orion_v3.work_loop.vault import ProjectVault, VaultError
from orion_v3.work_loop.contracts import WorkState, EvidenceRecord

def evidence():
    return EvidenceRecord("probe","task","a"*64,"execution","fail","probe","1")

class OrderingRecovery(unittest.TestCase):
    def setup(self,root):
        vault=ProjectVault(root)
        vault.initialize(WorkState("probe","qualification","start","task"))
        authority=SharedStop(root)
        authority.initialize()
        return vault,authority

    def test_commit_first_then_stop_persists(self):
        with tempfile.TemporaryDirectory() as root:
            vault,authority=self.setup(root)
            vault.record_verified_result(evidence(),next_action="done",commit_guard=authority.commit_guard)
            authority.stop()
            self.assertEqual(vault.load().last_verified_result,"execution:fail")
            self.assertTrue(SharedStop(root).stop_requested())
            with self.assertRaises(VaultError):
                vault.record_verified_result(evidence(),next_action="again",commit_guard=authority.commit_guard)
            print("COMMIT_FIRST_STOP_AFTER> PASS")

    def test_stop_first_commit_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            vault,authority=self.setup(root)
            authority.stop()
            with self.assertRaises(VaultError):
                vault.record_verified_result(evidence(),next_action="done",commit_guard=authority.commit_guard)
            self.assertEqual(vault.load().last_verified_result,"none")
            print("STOP_FIRST_COMMIT_DENIED> PASS")

    def test_pending_recovery_after_stop_is_not_a_new_commit(self):
        with tempfile.TemporaryDirectory() as root:
            vault,authority=self.setup(root)
            original=vault._write_state
            def interrupt(_):
                raise OSError("INJECTED_CRASH_AFTER_PENDING")
            vault._write_state=interrupt
            with self.assertRaises(OSError):
                vault.record_verified_result(evidence(),next_action="done",commit_guard=authority.commit_guard)
            vault._write_state=original
            self.assertTrue(vault.pending_path.exists())
            authority.stop()
            self.assertEqual(vault.load().last_verified_result,"execution:fail")
            first=vault.journal_path.read_text(encoding="utf-8")
            self.assertEqual(first.count("txid="),1)
            vault.load()
            self.assertEqual(vault.journal_path.read_text(encoding="utf-8"),first)
            print("PENDING_ACCEPTED_BEFORE_STOP_RECOVERY> PASS")

if __name__=="__main__":
    unittest.main(verbosity=2)
