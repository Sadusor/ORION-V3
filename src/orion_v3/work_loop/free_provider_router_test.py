import unittest
from orion_v3.work_loop.free_provider_router import Candidate, Failure, select_next

POOL = [Candidate("groq", "gpt-oss", "gpt-oss"),
        Candidate("openrouter", "gemma-free", "gemma"),
        Candidate("gemini", "flash", "gemini"),
        Candidate("paid", "premium", "other", False)]

class RouterTests(unittest.TestCase):
    def test_first(self):
        self.assertEqual(select_next(candidates=POOL)[0], POOL[0])
    def test_rate_limit_switch(self):
        self.assertEqual(select_next(candidates=POOL, failures=[Failure("groq","gpt-oss","RATE_LIMIT")])[0], POOL[1])
    def test_family_reserved(self):
        self.assertEqual(select_next(candidates=POOL, reserved_families={"gpt-oss","gemma"})[0], POOL[2])
    def test_stop(self):
        self.assertEqual(select_next(candidates=POOL, stop_requested=True)[1], "STOPPED")
    def test_budget(self):
        f=[Failure("groq","gpt-oss","RATE_LIMIT")]*4
        self.assertEqual(select_next(candidates=POOL, failures=f)[1], "ATTEMPT_BUDGET_EXHAUSTED")
    def test_auth_halts(self):
        self.assertEqual(select_next(candidates=POOL, failures=[Failure("groq","gpt-oss","AUTH")])[1], "NON_RECOVERABLE")
    def test_cooldown(self):
        self.assertEqual(select_next(candidates=POOL, cooldown_models={("groq","gpt-oss")})[0], POOL[1])
    def test_never_paid(self):
        self.assertIsNone(select_next(candidates=POOL, reserved_families={"gpt-oss","gemma","gemini"})[0])
    def test_unknown_failure_halts(self):
        self.assertEqual(select_next(candidates=POOL, failures=[Failure("groq","gpt-oss","WEIRD")])[1], "UNCLASSIFIED_FAILURE")
    def test_bad_budget(self):
        with self.assertRaises(ValueError): select_next(candidates=POOL, max_attempts=100)

if __name__ == "__main__": unittest.main()
