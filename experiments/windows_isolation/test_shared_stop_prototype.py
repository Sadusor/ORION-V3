import tempfile
import unittest
from shared_stop_prototype import SharedStop
from orion_v3.work_loop.vault import ProjectVault, VaultError
from orion_v3.work_loop.contracts import WorkState, EvidenceRecord

class Qualification(unittest.TestCase):
    def test_stop_blocks_real_vault(self):
        with tempfile.TemporaryDirectory() as root:
            vault = ProjectVault(root)
            vault.initialize(WorkState("probe", "qualification", "start", "task"))
            authority = SharedStop(root)
            authority.initialize()
            authority.stop()
            with self.assertRaises(VaultError):
                vault.record_verified_result(
                    EvidenceRecord("probe", "task", "a"*64, "execution", "fail", "probe", "1"),
                    next_action="done", commit_guard=authority.commit_guard)
            self.assertEqual(vault.load().last_verified_result, "none")
            print("REAL_VAULT_SHARED_STOP> PASS")

if __name__ == "__main__":
    unittest.main(verbosity=2)
