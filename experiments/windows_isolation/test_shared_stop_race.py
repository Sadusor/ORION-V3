"""Concurrent STOP versus real Vault commit, disposable experiment only."""
import multiprocessing as mp
import tempfile
import unittest
from shared_stop_prototype import SharedStop
from orion_v3.work_loop.vault import ProjectVault, VaultError
from orion_v3.work_loop.contracts import WorkState, EvidenceRecord

def contender(root, start, queue, role):
    if not start.wait(10):
        queue.put((role, "TIMEOUT"))
        return
    try:
        if role == "stop":
            SharedStop(root).stop()
            queue.put((role, "OK"))
        else:
            ProjectVault(root).record_verified_result(
                EvidenceRecord("probe", "task", "a"*64, "execution", "fail", "probe", "1"),
                next_action="done", commit_guard=SharedStop(root).commit_guard)
            queue.put((role, "COMMITTED"))
    except VaultError:
        queue.put((role, "REJECTED"))
    except Exception as exc:
        queue.put((role, type(exc).__name__))

class RaceQualification(unittest.TestCase):
    def test_concurrent_stop_and_commit(self):
        ctx=mp.get_context("spawn")
        for iteration in range(12):
            with self.subTest(iteration=iteration), tempfile.TemporaryDirectory() as root:
                vault=ProjectVault(root)
                vault.initialize(WorkState("probe","race","start","task"))
                SharedStop(root).initialize()
                start=ctx.Event()
                queue=ctx.Queue()
                processes=[ctx.Process(target=contender,args=(root,start,queue,role))
                           for role in ("stop","commit")]
                for process in processes: process.start()
                try:
                    start.set()
                    observed=dict(queue.get(timeout=15) for _ in processes)
                    for process in processes:
                        process.join(timeout=5)
                        self.assertEqual(process.exitcode,0)
                    self.assertEqual(observed["stop"],"OK")
                    self.assertIn(observed["commit"],("REJECTED","COMMITTED"))
                    self.assertTrue(SharedStop(root).stop_requested())
                    state=vault.load()
                    if observed["commit"]=="REJECTED":
                        self.assertEqual(state.last_verified_result,"none")
                    else:
                        self.assertEqual(state.last_verified_result,"execution:fail")
                    print("STOP_COMMIT_RACE_ITERATION> %02d %s" % (iteration, observed["commit"]))
                finally:
                    start.set()
                    for process in processes:
                        if process.is_alive(): process.terminate()
                        process.join(timeout=3)
        print("STOP_COMMIT_RACE_REAL_VAULT> PASS_12")
        print("COMMIT_LINEARIZATION_AND_CRASH> NOT_QUALIFIED")

if __name__=="__main__":
    unittest.main(verbosity=2)
