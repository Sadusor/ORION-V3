"""Cross-process STOP gap probe against actual ORION coordinator and Vault.

Expected finding: an in-process STOP is not visible to an independent process.
A passing probe is a DIAGNOSTIC, never security qualification.
"""
import multiprocessing as mp
import tempfile
import unittest
from pathlib import Path
from orion_v3.work_loop.commit_coordinator import CommitCoordinator
from orion_v3.work_loop.contracts import WorkState, EvidenceRecord
from orion_v3.work_loop.vault import ProjectVault

def other_process(root, gate, results):
    from orion_v3.work_loop.commit_coordinator import CommitCoordinator
    from orion_v3.work_loop.vault import ProjectVault
    from orion_v3.work_loop.contracts import EvidenceRecord
    local = CommitCoordinator()
    generation = local.snapshot()
    gate.wait(timeout=10)
    try:
        ProjectVault(root).record_verified_result(
            EvidenceRecord("probe", "task", "a"*64, "execution", "fail", "probe", "1"),
            next_action="done", commit_coordinator=local, expected_generation=generation
        )
        results.put("COMMITTED")
    except Exception as e:
        results.put("REJECTED:"+type(e).__name__)

class CrossProcessStopGap(unittest.TestCase):
    def test_stop_not_shared_across_processes(self):
        with tempfile.TemporaryDirectory(prefix="orion-stop-gap-") as root:
            vault=ProjectVault(root)
            vault.initialize(WorkState("probe","diagnostic","start","task"))
            ctx=mp.get_context("spawn")
            gate=ctx.Event()
            results=ctx.Queue()
            child=ctx.Process(target=other_process,args=(root,gate,results))
            child.start()
            try:
                owner=CommitCoordinator()
                owner.stop()
                gate.set()
                result=results.get(timeout=15)
                child.join(timeout=5)
                self.assertEqual(child.exitcode,0)
                self.assertEqual(result,"COMMITTED",
                    "Coordinator behavior changed; investigate before drawing conclusions")
                self.assertIn("txid=",vault.journal_path.read_text(encoding="utf-8"))
                print("CROSS_PROCESS_STOP_GAP> CONFIRMED")
                print("REAL_STOP_SERVICE_INTEGRATION> NOT_TESTED")
                print("SECURITY_QUALIFICATION> BLOCKED")
                print("REAL_ORION_EXECUTION> DISABLED")
            finally:
                if child.is_alive():child.terminate()
                child.join(timeout=3)

if __name__=="__main__":
    unittest.main(verbosity=2)
