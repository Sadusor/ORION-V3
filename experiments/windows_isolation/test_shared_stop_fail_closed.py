"""Fail-closed shared STOP authority checks against disposable real Vault."""
import os
import tempfile
import unittest
from shared_stop_prototype import SharedStop
from orion_v3.work_loop.vault import ProjectVault, VaultError
from orion_v3.work_loop.contracts import WorkState, EvidenceRecord

def attempt(vault, stop):
    vault.record_verified_result(
        EvidenceRecord("probe","task","a"*64,"execution","fail","probe","1"),
        next_action="done",commit_guard=stop.commit_guard)

class StopAuthorityFailClosed(unittest.TestCase):
    def setup(self,root):
        vault=ProjectVault(root)
        vault.initialize(WorkState("probe","qualification","start","task"))
        stop=SharedStop(root)
        stop.initialize()
        return vault,stop

    def test_missing_authority_blocks_commit(self):
        with tempfile.TemporaryDirectory() as root:
            vault,stop=self.setup(root)
            os.unlink(stop.db)
            with self.assertRaises((RuntimeError,VaultError)):
                attempt(vault,stop)
            self.assertEqual(vault.load().last_verified_result,"none")
            print("STOP_AUTHORITY_MISSING> FAIL_CLOSED")

    def test_corrupt_authority_blocks_commit(self):
        with tempfile.TemporaryDirectory() as root:
            vault,stop=self.setup(root)
            with open(stop.db,"wb") as f: f.write(b"invalid sqlite header")
            with self.assertRaises((RuntimeError,VaultError)):
                attempt(vault,stop)
            self.assertEqual(vault.load().last_verified_result,"none")
            print("STOP_AUTHORITY_CORRUPT> FAIL_CLOSED")

    def test_stop_survives_reinitialization(self):
        with tempfile.TemporaryDirectory() as root:
            vault,stop=self.setup(root)
            stop.stop()
            SharedStop(root).initialize()
            self.assertTrue(SharedStop(root).stop_requested())
            with self.assertRaises((RuntimeError,VaultError)):
                attempt(vault,SharedStop(root))
            self.assertEqual(vault.load().last_verified_result,"none")
            print("STOP_AUTHORITY_PERSISTENT> PASS")

if __name__=="__main__":
    unittest.main(verbosity=2)
