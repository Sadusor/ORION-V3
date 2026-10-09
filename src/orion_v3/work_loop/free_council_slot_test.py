import unittest
from orion_v3.work_loop.free_provider_router import Candidate
from orion_v3.work_loop.free_council_slot import run_slot
from orion_v3.work_loop.openrouter_text_adapter import CloudRequestError

POOL=[Candidate("groq","gpt-oss","gpt-oss"),Candidate("openrouter","gemma","gemma"),
      Candidate("gemini","flash","gemini")]

class SlotTests(unittest.TestCase):
    def test_first_success(self):
        r=run_slot(candidates=POOL,invoke=lambda c:"proposal",stop_requested=lambda:False)
        self.assertEqual((r["status"],r["selected"].provider),("COMPLETED","groq"))
    def test_rate_limit_fallback(self):
        def invoke(c):
            if c.provider=="groq":raise CloudRequestError("RATE_LIMIT")
            return "proposal"
        r=run_slot(candidates=POOL,invoke=invoke,stop_requested=lambda:False)
        self.assertEqual([x["status"] for x in r["evidence"]],["RATE_LIMIT","COMPLETED"])
    def test_family_independence(self):
        r=run_slot(candidates=POOL,invoke=lambda c:"proposal",stop_requested=lambda:False,
                   reserved_families={"gpt-oss","gemma"})
        self.assertEqual(r["selected"].family,"gemini")
    def test_stop_before(self):
        self.assertEqual(run_slot(candidates=POOL,invoke=lambda c:"x",stop_requested=lambda:True)["status"],"STOPPED")
    def test_stop_after(self):
        stop=[False]
        def invoke(c):
            stop[0]=True
            return "proposal"
        self.assertEqual(run_slot(candidates=POOL,invoke=invoke,stop_requested=lambda:stop[0])["status"],"STOPPED")
    def test_auth_halts(self):
        def invoke(c):raise CloudRequestError("AUTH")
        r=run_slot(candidates=POOL,invoke=invoke,stop_requested=lambda:False)
        self.assertEqual((r["status"],len(r["evidence"])),("NON_RECOVERABLE",1))
    def test_unknown_halts_without_leak(self):
        def invoke(c):raise RuntimeError("SECRET_PRIVATE")
        r=run_slot(candidates=POOL,invoke=invoke,stop_requested=lambda:False)
        self.assertEqual(r["status"],"UNCLASSIFIED_FAILURE")
        self.assertNotIn("SECRET_PRIVATE",str(r))
    def test_budget(self):
        def invoke(c):raise CloudRequestError("PROVIDER")
        r=run_slot(candidates=POOL,invoke=invoke,stop_requested=lambda:False,max_attempts=2)
        self.assertEqual((r["status"],len(r["evidence"])),("ATTEMPT_BUDGET_EXHAUSTED",2))
    def test_invalid_response_halts(self):
        r=run_slot(candidates=POOL,invoke=lambda c:"",stop_requested=lambda:False)
        self.assertEqual(r["status"],"NON_RECOVERABLE")

if __name__=="__main__":unittest.main()
