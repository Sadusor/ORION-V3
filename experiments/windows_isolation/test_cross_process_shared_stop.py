"""Cross-process shared STOP diagnostic against the real Vault (disposable only)."""
import multiprocessing as mp
import tempfile
import unittest
from shared_stop_prototype import SharedStop
from orion_v3.work_loop.vault import ProjectVault, VaultError
from orion_v3.work_loop.contracts import WorkState, EvidenceRecord

def worker(root, ready, proceed, results):
    ready.set()
    if not proceed.wait(10):
        results.put("TIMEOUT")
        return
    try:
        ProjectVault(root).record_verified_result(
            EvidenceRecord("probe","task","a"*64,"execution","fail","probe","1"),
            next_action="done",commit_guard=SharedStop(root).commit_guard)
        results.put("COMMITTED")
    except VaultError:
        results.put("REJECTED")

class CrossProcessSharedStop(unittest.TestCase):
    def test_stop_in_parent_blocks_child_commit(self):
        with tempfile.TemporaryDirectory() as root:
            vault=ProjectVault(root)
            vault.initialize(WorkState("probe","qualification","start","task"))
            stop=SharedStop(root)
            stop.initialize()
            ctx=mp.get_context("spawn")
            ready=ctx.Event()
            proceed=ctx.Event()
            results=ctx.Queue()
            child=ctx.Process(target=worker,args=(root,ready,proceed,results))
            child.start()
            try:
                self.assertTrue(ready.wait(10))
                stop.stop()
                proceed.set()
                outcome=results.get(timeout=15)
                child.join(timeout=5)
                self.assertEqual(child.exitcode,0)
                self.assertEqual(outcome,"REJECTED")
                self.assertEqual(vault.load().last_verified_result,"none")
                print("CROSS_PROCESS_SHARED_STOP_REAL_VAULT> PASS")
            finally:
                proceed.set()
                if child.is_alive():child.terminate()
                child.join(timeout=3)

if __name__=="__main__":
    unittest.main(verbosity=2)
